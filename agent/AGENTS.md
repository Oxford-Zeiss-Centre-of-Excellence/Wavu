<!-- Generated from agent/skills/wavu/SKILL.md by tools/make_agent_files.py; edit that file instead. -->
<!-- Wavu agent instructions: https://oxford-zeiss-centre-of-excellence.github.io/Wavu/agents/ -->

# The Wavu way

Wavu (https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu) runs a plain Python file from an image viewer:
Fiji (wavu-fiji) or napari (wavu-napari). The viewer builds a dialog from the script's `PARAMS`, a local worker runs `run(ctx, inputs, params)` inside the **script folder's own
pixi environment**, and the returned values open in the viewer as images, tables or ROIs (napari: Image, Labels
and Shapes layers). The same script folder works in both viewers. The user may be an image analyst
who knows notebooks better than software engineering: keep scripts short, plain and well commented.

A script folder (start from https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu-Script-Template):

| File | Role |
|---|---|
| `script.py` | `PARAMS` (the dialog) and `run(ctx, inputs, params)` (the work). Any top-level `*.py` with `def run` is a script. |
| `test_script.py` | Tests that run without a viewer: `pixi run test` |
| `pixi.toml` / `pixi.lock` | This script's own environment. Commit both. |
| `.vscode/launch.json` | "Attach to Wavu worker" for breakpoints |

## The steps, in order

| Step | What | Where |
|---|---|---|
| 0 | **Write the test first**: a made-up image with a known answer | `test_script.py` |
| 1 | Describe the dialog | `PARAMS` |
| 2 | Do the work, reporting progress | `run(ctx, inputs, params)` |
| 3 | Return what the viewer should show | the returned `dict` |
| 4 | Add packages (conda-forge first) | `pixi.toml` |
| 5 | Run the tests until green, then try it in Fiji or napari | `pixi run test` |
| 6 | Share it as a Fiji menu item | `pixi run wavu package` |
| 7 | Optional: share it as a container | `Dockerfile` |

## Step 0: tests first

Before changing `script.py`, write or extend a test that states what a correct result must be. Build a small
synthetic image whose answer you know (two separate squares → 2 labels; one bright pixel → blur lowers its peak;
a stack → same shape back). Run it and see it **fail** first, then make it pass.

```python
from pathlib import Path
import numpy as np
from wavu.testing import FakeCtx, run_script

SCRIPT = Path(__file__).with_name("script.py")


def test_two_blobs_give_two_labels():
    img = np.zeros((40, 40), np.uint16)
    img[5:12, 5:12] = 1000
    img[25:33, 20:30] = 1000                    # two separate bright squares
    ctx = FakeCtx()
    out = run_script(SCRIPT, {"image": img}, {"threshold": 500}, ctx=ctx)
    assert out["labels"].max() == 2              # two objects found
    assert out["labels"].shape == img.shape      # same size as the input
    assert ctx.progress_values[-1] == 1.0        # progress reached 100 %
```

- `run_script` calls `run` exactly as the worker does: `PARAMS` defaults filled in, values converted to the declared
  types.
- `FakeCtx` records `ctx.messages` and `ctx.progress_values`; `FakeCtx(cancel_after=2)` simulates the user pressing
  Esc; `FakeCtx(meta={"image": {"pixel_um": 0.5}})` supplies input metadata.
- **Never weaken or delete a test to make it pass.** A red test means the script, or the test's assumption, is wrong:
  say which, and fix that.

## Step 1: `PARAMS` is the dialog

```python
"""Nuclei count -- threshold, label, measure."""   # first docstring line = dialog description

PARAMS = {
    "image":     {"type": "image", "label": "Nuclei image"},
    "threshold": {"type": "float", "default": 500.0, "label": "Threshold (intensity)"},
    "min_area":  {"type": "int",   "default": 20},
    "name":      {"type": "str",   "default": "cells"},
    "fill":      {"type": "bool",  "default": True},
    "method":    {"type": "choice", "choices": ["otsu", "li"], "default": "otsu"},
}
```

- Types: `float`, `int`, `str`, `bool`, `choice` (needs `choices`), `image` (an open image or layer; arrives in
  `inputs`, not `params`).
- Every non-image entry needs a `default`. `label` is optional (defaults to the capitalised name).

## Step 2: `run(ctx, inputs, params)`

- `inputs["image"]` is a `numpy.ndarray` in ImageJ axis order with singleton axes dropped: `T, Z, C, Y, X`
  (+ `S` for RGB). Check `ndim` and raise `ValueError("...")` with a plain sentence if the shape is wrong; the viewer shows
  the message as is.
- `ctx.meta["image"]` holds `pixel_um`, `axes`, `title` when the viewer knows them.
- `ctx.log(msg)` writes to the viewer's log (Fiji's Log window, the napari panel); `ctx.progress(0..1)` drives the progress bar; check `ctx.cancelled()` in
  loops and return early (cancelling is cooperative); `ctx.tmpdir` is a scratch folder for files you return.
- **Import heavy packages inside `run`** (cellpose, torch, skimage), so the viewer lists the script and shows its dialog
  instantly. Log a line before slow first-time work such as model downloads.
- Prefer vectorised NumPy/scikit-image over Python loops over pixels.

## Step 3: what to return

| Return value | Fiji shows (napari: a layer or panel) |
|---|---|
| `numpy` array (≥ 2-D) | a new image (bool → 8-bit, ints ≤ 65535 → 16-bit, else 32-bit float) |
| an integer array named like `labels` | a label image with the glasbey colours |
| `wavu.Image(arr, pixel_um=0.65, axes="ZYX", channel_names=[...])` | an image with calibration and axes |
| pandas `DataFrame` or a list of dicts | a Results table |
| `wavu.RoiSet(path_to_zip)` | the ROI Manager (write the zip with `roifile` into `ctx.tmpdir`) |
| number, string, bool | a `name = value` line in the Log |
| `pathlib.Path` | the path, printed in the Log |

## Step 4: packages

- Add packages to `pixi.toml`. **conda-forge first** under `[dependencies]` (`pixi add scikit-image`); only if a
  package is not on conda-forge, use `[pypi-dependencies]` (`pixi add --pypi name`). Names can differ:
  `pytorch` on conda-forge, `torch` on PyPI.
- Keep the line marked `# wavu-dependency` as it is. Commit `pixi.lock` with `pixi.toml`.

## Step 5: run and try

```bash
pixi run test                                                   # red first, then green
pixi run wavu run script.py --in image=cells.tif --param threshold=400 --out results   # whole script on a file
```

Then in Fiji: **Plugins › Wavu › Stop Worker** (the worker reads scripts only when it starts), then
**Plugins › Wavu › Run Python Script** and pick the folder. In napari (`pixi run -e napari napari` in a Wavu
clone): **Plugins › Run Python Script (Wavu)**, choose the folder, **Start worker** (press **Stop worker** after
editing the script), then **Run**. For breakpoints: `pixi run debug`, attach VS Code with
"Attach to Wavu worker", then **Plugins › Wavu › Connect to Running Worker**.

## Step 6: share

```bash
pixi install                                                    # makes sure pixi.lock exists
pixi run wavu package . --name my-tool --menu "My Lab>My Tool"  # -> dist/my-tool-fiji.zip
```

Colleagues unzip the zip into `Fiji.app` (Wavu must be installed) and get **Plugins › My Lab › My Tool**.

## Step 7 (optional): container

For locked-down PCs, a lab server or HPC. The template's `Dockerfile` installs exactly `pixi.lock` (commit it) and
fetches wavu from GitHub, so it works only in template copies, not inside the Wavu repository (there: Wavu's root
`Dockerfile` with `--build-arg SCRIPT_DIR=...`). `wavu package` leaves `Dockerfile`/`.dockerignore` out of the Fiji zip.
Any OCI tool works with the same `build`/`run` words: Docker or Podman; on macOS also Apple's `container` (Apple
silicon), OrbStack or Colima; on Windows through WSL 2 (Podman/Docker Engine inside it, or Podman/Rancher Desktop).
On HPC: `apptainer pull docker://ghcr.io/<you>/<tool>:<version>`.

```bash
docker build -t my-tool .
docker run --rm -p 127.0.0.1:8765:8765 -e WAVU_TOKEN=pick-one -v /my/data:/data my-tool
```

The worker writes `/my/data/.wavu/worker.json` and job files under `/my/data/.wavu-tmp`. Connect with handshake file
`/my/data/.wavu/worker.json`, host folder `/my/data`, container folder `/data`: in Fiji via **Plugins › Wavu › Connect
to Running Worker**; in napari tick **Remote / container** (fields Handshake file, Host (empty = address in the file),
Host folder, Container folder), then **Connect to running worker**. In Python:
`Worker.connect(handshake, host=None, host_prefix="/my/data", worker_prefix="/data")`. The token is the only
protection: keep it secret, prefer `127.0.0.1` or an SSH tunnel. Wavu publishes no images of user scripts; the user
pushes their own (e.g. `ghcr.io/<user>/<tool>:1.0.0`). Guide:
https://oxford-zeiss-centre-of-excellence.github.io/Wavu/write/container/

## Converting existing code

Turning a napari plugin, a notebook or a Fiji macro into a script folder:

1. **Start from the template** and find the algorithm core: the function(s) that take an array and return a result.
2. **Drop the UI code** (magicgui, Qt, `napari` imports, widgets, `ipywidgets`, macro dialogs). `PARAMS` replaces
   the UI: each user-set value becomes one entry, with the original default.
3. **Map the data to the contract**: layers or opened images become `image` inputs (`T, Z, C, Y, X` order); results
   become returned arrays, `wavu.Image`, tables or `wavu.RoiSet`. Replace prints with `ctx.log`, add `ctx.progress`
   and `ctx.cancelled()` checks.
4. **Move dependencies to `pixi.toml`**, conda-forge first; drop napari, Qt and magicgui. The script then runs in its
   own isolated environment, without clashing with napari's or other plugins', and from Fiji too.
5. **Tests first**: reuse the original project's test data and expected results if it has any, otherwise a
   synthetic image; check the converted script reproduces the original's output.
6. **Keep credit**: a comment at the top of `script.py` naming the original repository, its authors and its
   licence; respect that licence's terms.

## Scripted workflows (batch, end to end)

A Wavu script is also a function call. When the user wants a whole folder analysed, write a pipeline in their
own tool that does the native steps itself and calls Wavu only for the heavy step (each call runs in that
script folder's own environment; the worker starts once and is reused):

- **Fiji Groovy:** `def wavu = new GroovyShell(this.class.classLoader).evaluate(new File(IJ.getDirectory("imagej"),
  "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt"))`, then per image
  `Map r = wavu.run(folder, "script", [diameter: 30], [image: imp])` → `r.images` (ImagePlus), `r.tables`
  (ResultsTable), `r.rois` (RoiSet zip path), `r.values`; `wavu.stopAll()` at the end. Throws on failure.
- **ImageJ macro:** `run("Run Script (Macro)", "folder=[/path/to/folder] script=script params=[diameter=30]");`
  — image parameters get the current image (also under `setBatchMode(true)`); results open as
  `<title>-<output>` windows, ROIs in the ROI Manager, numbers in the Log. Values have no spaces.
- **Python / napari:** `with Worker.start(folder) as w:` then `res = w.run("script", params, {"image": img})`;
  `res.outputs[name].value`. The notebook's own environment needs no heavy packages.

Keep native steps native (Fiji filters and measurements, scikit-image, pandas) and write one CSV for the folder.

## Scope and limits

- Small, interactive data: one image that fits in memory (about 1–2 GB at most). For larger data suggest a batch
  or HPC workflow instead of Wavu.
- Do not write Java, Groovy, Fiji or napari plugin code; wavu-fiji and wavu-napari already exist. Everything
  happens in the script, in Python.
- The environment isolates dependencies; it is not a security sandbox.

## Checklist before you finish

- [ ] `test_script.py` states the expected result, ran red first, and `pixi run test` is now green.
- [ ] `PARAMS` has a default for every non-image field and readable labels; the docstring's first line says what
      the script does.
- [ ] Heavy imports are inside `run`; long loops check `ctx.cancelled()`; progress reaches 1.0.
- [ ] New packages are in `pixi.toml` (conda-forge first) and `pixi.lock` is updated.
- [ ] You told the user how to try it: **Stop Worker**, then **Run Python Script**.
