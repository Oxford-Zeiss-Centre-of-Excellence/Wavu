"""The Wavu dock widget: pick a script folder, fill in its PARAMS, run it in its own pixi env."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from magicgui import widgets
from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import QTableWidget, QTableWidgetItem

from napari_wavu._convert import layer_input, output_layers, table_rows

if TYPE_CHECKING:
    import napari

IMAGE_LAYER_TYPES = ("Image", "Labels")


class _Bridge(QObject):
    """Signals emitted from worker threads; Qt delivers them on the GUI thread."""

    log = Signal(str)
    progress = Signal(float)


def param_widget(name: str, spec: dict[str, Any], layer_choices: Any) -> widgets.Widget:
    """One magicgui widget for a PARAMS entry (see the Wavu script contract)."""
    label = spec.get("label") or name.replace("_", " ").capitalize()
    t = spec.get("type")
    default = spec.get("default")
    if t == "image":
        return widgets.ComboBox(name=name, label=label, choices=layer_choices)
    if t == "float":
        return widgets.FloatSpinBox(name=name, label=label, value=float(default), min=-1e12, max=1e12, step=0.1)
    if t == "int":
        return widgets.SpinBox(name=name, label=label, value=int(default), min=-2**31, max=2**31 - 1)
    if t == "bool":
        return widgets.CheckBox(name=name, label=label, value=bool(default))
    if t == "choice":
        choices = list(spec.get("choices") or [])
        return widgets.ComboBox(name=name, label=label, choices=choices, value=default if default in choices else choices[0])
    return widgets.LineEdit(name=name, label=label, value="" if default is None else str(default))


class WavuWidget(widgets.Container):
    def __init__(self, napari_viewer: "napari.viewer.Viewer"):
        super().__init__(labels=False)
        self.viewer = napari_viewer
        self._workers: dict[str, Any] = {}  # script folder -> wavu.client.Worker
        self._schemas: dict[str, Any] = {}
        self._cancel: threading.Event | None = None
        self._defaults: dict[str, Any] = {}  # input pixel size, applied to image outputs
        self._bridge = _Bridge()
        self._bridge.log.connect(self._append_log)
        self._bridge.progress.connect(lambda v: setattr(self._progress, "value", int(v * 100)))

        self._folder = widgets.FileEdit(mode="d", label="Script folder")
        self._start = widgets.PushButton(text="Start worker")
        self._connect = widgets.PushButton(text="Connect to running worker")
        self._script = widgets.ComboBox(label="Script", choices=[])
        self._doc = widgets.Label(value="")
        self._params = widgets.Container(labels=True)
        self._run = widgets.PushButton(text="Run")
        self._stop_job = widgets.PushButton(text="Cancel", enabled=False)
        self._progress = widgets.ProgressBar(value=0, min=0, max=100)
        self._log = widgets.TextEdit(value="")
        self._log.read_only = True
        self._stop_worker = widgets.PushButton(text="Stop worker")
        self._active: str | None = None  # key of the worker in use (folder, or host:port when connected)

        # Remote / container: attach to a worker started elsewhere (docker run, another machine).
        self._remote = widgets.CheckBox(text="Remote / container", value=False)
        self._handshake = widgets.FileEdit(mode="r", filter="*.json", label="Handshake file",
                                           value=str(Path.home() / ".wavu" / "worker.json"))
        self._host = widgets.LineEdit(label="Host", value="", tooltip="Empty: use the address in the handshake file")
        self._host_dir = widgets.FileEdit(mode="d", label="Host folder", value="",
                                          tooltip="Shared folder on this machine, e.g. D:/data (empty: none)")
        self._worker_dir = widgets.LineEdit(label="Container folder", value="",
                                            tooltip="The same folder as the worker sees it, e.g. /data")
        self._remote_box = widgets.Container(
            widgets=[self._handshake, self._host, self._host_dir, self._worker_dir], labels=True, visible=False)

        top = widgets.Container(widgets=[self._folder], labels=True)
        buttons = widgets.Container(widgets=[self._start, self._connect], layout="horizontal", labels=False)
        script = widgets.Container(widgets=[self._script], labels=True)
        run = widgets.Container(widgets=[self._run, self._stop_job], layout="horizontal", labels=False)
        self.extend([top, buttons, self._remote, self._remote_box, script, self._doc, self._params, run,
                     self._progress, self._log, self._stop_worker])
        self._remote.changed.connect(lambda on: setattr(self._remote_box, "visible", bool(on)))

        self._start.changed.connect(self._on_start)
        self._connect.changed.connect(self._on_connect)
        self._script.changed.connect(self._on_script)
        self._run.changed.connect(self._on_run)
        self._stop_job.changed.connect(self._on_cancel)
        self._stop_worker.changed.connect(self._on_stop_worker)
        self._set_ready(False)
        # Keep the image drop-downs in step with the layer list (napari also does
        # this for docked widgets; doing it here makes the panel self-contained).
        for ev in (napari_viewer.layers.events.inserted, napari_viewer.layers.events.removed):
            ev.connect(lambda *_: self._params.reset_choices())

    # -- helpers -----------------------------------------------------------
    def _layer_choices(self, _widget: Any = None) -> list[tuple[str, Any]]:
        return [(layer.name, layer) for layer in self.viewer.layers if type(layer).__name__ in IMAGE_LAYER_TYPES]

    def _append_log(self, msg: str) -> None:
        self._log.value = (self._log.value + "\n" + msg).lstrip("\n")
        bar = self._log.native.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _set_ready(self, ready: bool) -> None:
        for w in (self._script, self._run, self._stop_worker):
            w.enabled = ready

    def _set_busy(self, busy: bool) -> None:
        for w in (self._start, self._connect, self._run, self._script, self._stop_worker):
            w.enabled = not busy
        self._stop_job.enabled = busy

    @property
    def worker(self) -> Any:
        return self._workers.get(self._active) if self._active else None

    # -- worker lifecycle ----------------------------------------------------
    def _on_start(self) -> None:
        from wavu.client import Worker

        folder = Path(self._folder.value)
        known = self._workers.get(str(folder))
        if known is not None and known.alive():
            self._active = str(folder)
            self._load_scripts(known)
            return
        self._cancel = threading.Event()
        self._background(Worker.start, folder, on_log=self._bridge.log.emit, cancel=self._cancel,
                         on_done=lambda w: self._attach(str(folder), w))

    def _on_connect(self) -> None:
        from wavu.client import Worker, WorkerError

        kwargs: dict[str, Any] = {}
        if self._remote.value:
            host_dir = str(self._host_dir.value or "").strip()
            worker_dir = str(self._worker_dir.value or "").strip()
            if bool(host_dir and host_dir != ".") != bool(worker_dir):
                self._failed(ValueError("give both the host folder and the container folder, or neither"))
                return
            kwargs = {"handshake": self._handshake.value, "host": self._host.value.strip() or None,
                      "host_prefix": host_dir if worker_dir else None, "worker_prefix": worker_dir or None}
        try:
            w = Worker.connect(**kwargs)
        except (WorkerError, OSError, ValueError) as e:
            self._failed(e)
            return
        where = f" (host folder {w.host_prefix} = {w.worker_prefix})" if w.host_prefix else ""
        self._append_log(f"Connected to the worker at {w.host}:{w.port} serving {w.script_dir}{where}")
        self._attach(f"connected:{w.host}:{w.port}", w)

    def _attach(self, key: str, w: Any) -> None:
        self._workers[key] = w
        self._active = key
        self._load_scripts(w)

    def _load_scripts(self, w: Any) -> None:
        listing = w.scripts()
        for name, err in listing.get("errors", {}).items():
            self._append_log(f"Could not load {name}: {err}")
        self._schemas = listing.get("scripts", {})
        self._script.choices = sorted(self._schemas)
        self._set_ready(bool(self._schemas))
        if self._schemas:
            self._on_script()

    def _on_stop_worker(self) -> None:
        w = self._workers.pop(self._active, None) if self._active else None
        self._active = None
        if w is not None:
            w.stop()
            self._append_log("Worker stopped.")
        self._script.choices = []
        self._params.clear()
        self._set_ready(False)

    def stop_all(self) -> None:
        for w in self._workers.values():
            w.stop()
        self._workers.clear()

    # -- running -------------------------------------------------------------
    def _on_script(self, *_: Any) -> None:
        schema = self._schemas.get(self._script.value) or {}
        self._doc.value = (schema.get("doc") or "").strip().splitlines()[0] if schema.get("doc") else ""
        self._params.clear()
        for name, spec in (schema.get("params") or {}).items():
            self._params.append(param_widget(name, spec, self._layer_choices))

    def _on_run(self) -> None:
        w = self.worker
        if w is None:
            self._failed(RuntimeError("start a worker first"))
            return
        script = self._script.value
        params: dict[str, Any] = {}
        inputs: dict[str, Any] = {}
        meta: dict[str, dict] = {}
        for pw in self._params:
            spec = self._schemas[script]["params"][pw.name]
            if spec.get("type") == "image":
                if pw.value is None:
                    self._failed(RuntimeError(f"{pw.label}: open an image layer first"))
                    return
                inputs[pw.name], meta[pw.name] = layer_input(pw.value)
            else:
                params[pw.name] = pw.value
        self._cancel = threading.Event()
        self._progress.value = 0
        px = next((m["pixel_um"] for m in meta.values() if m.get("pixel_um")), None)
        self._defaults = {"pixel_um": px} if px else {}
        self._append_log(f"Running {script}...")
        self._background(w.run, script, params, inputs, meta=meta, on_log=self._bridge.log.emit,
                         on_progress=self._bridge.progress.emit, cancel=self._cancel,
                         on_done=self._show_result)

    def _on_cancel(self) -> None:
        if self._cancel is not None:
            self._cancel.set()
            self._append_log("Cancelling...")

    def _background(self, fn: Any, *args: Any, on_done: Any, **kwargs: Any) -> None:
        """Run fn in a thread; errors go to the log (never raised into Qt's event loop)."""
        from napari.qt.threading import create_worker

        def task() -> tuple[bool, Any]:
            try:
                return True, fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001 - shown to the user in the panel
                return False, e

        self._set_busy(True)
        job = create_worker(task, _start_thread=False)
        job.returned.connect(lambda r: on_done(r[1]) if r[0] else self._failed(r[1]))
        job.finished.connect(lambda: self._set_busy(False))
        job.start()

    def _show_result(self, result: Any) -> None:
        layers, notes = output_layers(result.outputs, self._defaults)
        for data, kwargs, kind in layers:
            getattr(self.viewer, f"add_{kind}")(data, **kwargs)
        for note in notes:
            self._append_log(note)
        for name, out in result.outputs.items():
            if out.kind == "table":
                self._show_table(name, out.value)
        self._progress.value = 100
        self._append_log("Done.")

    def _show_table(self, name: str, value: Any) -> None:
        cols, rows = table_rows(value)
        table = QTableWidget(len(rows), len(cols))
        table.setHorizontalHeaderLabels(cols)
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(v)))
        self.viewer.window.add_dock_widget(table, name=name, area="right", tabify=True)

    def _failed(self, err: BaseException) -> None:
        from wavu.client import JobCancelled

        if isinstance(err, JobCancelled):  # the user pressed Cancel: not an error
            self._append_log("Cancelled.")
            return
        self._append_log(f"Error: {err}")
        try:
            from napari.utils.notifications import show_error

            show_error(str(err).splitlines()[0])
        except Exception:  # noqa: BLE001 - notifications are best effort
            pass
