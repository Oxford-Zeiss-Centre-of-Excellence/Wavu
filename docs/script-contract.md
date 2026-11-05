# The Wavu script contract

A **script folder** contains:

- `pixi.toml`: the folder's own environment. It must depend on `wavu`.
- one or more scripts (`*.py`, see below),
- optionally, helper modules, tests and `.vscode/launch.json`.

Start from [`templates/wavu-script`](../templates/wavu-script). You can copy
it by hand, or run `pixi run new-script <name>` in a clone of this repo, or
`wavu new-script <name>` anywhere wavu is installed.

## Which files are scripts

The worker treats every top-level `*.py` file in the folder as a script if it
defines `run`. These files are skipped: names starting with `_`, `.` or
`test_`, names ending in `_test.py`, `conftest.py`, and files without
`def run`. The script folder is put on `sys.path`, so `import helpers` works.
A script that fails to import is listed in `GET /scripts` → `errors`, and
Fiji shows the error in the Log.

## `PARAMS`

```python
PARAMS = {
    "image":   {"type": "image", "label": "Nuclei image"},
    "sigma":   {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
    "n":       {"type": "int",   "default": 3},
    "name":    {"type": "str",   "default": "cells"},
    "fast":    {"type": "bool",  "default": True},
    "method":  {"type": "choice", "choices": ["otsu", "li"], "default": "otsu"},
}
```

| type | Fiji dialog field | value passed to `run` |
|---|---|---|
| `float` | numeric field | `float` |
| `int` | numeric field (0 decimals) | `int` |
| `str` | text field | `str` |
| `bool` | checkbox | `bool` |
| `choice` | drop-down (`choices` required) | `str` |
| `image` | drop-down of open images | `inputs[name]`: a numpy array (not in `params`) |

- `default` is required, except for `image`. For `choice`, `default` falls
  back to the first item.
- `label` defaults to the name, capitalised, with `_` replaced by spaces.
- The module docstring's first line is shown at the top of the dialog.
- Values from Fiji, the CLI or a request are converted to the declared type.
  Unknown names and invalid values are rejected before `run` is called.

## `run(ctx, inputs, params) -> dict`

### `inputs`

- An image sent inline, or as a `.tif`/`.tiff` path, arrives as a
  **`numpy.ndarray`**. The axes are in ImageJ order with singleton axes
  dropped: `T, Z, C, Y, X`, plus a final RGB sample axis `S` for RGB images.
  Fiji sends `uint8`, `uint16`, `float32` or RGB `uint8`.
- A `.csv` path arrives as a pandas `DataFrame`, or as a list of dicts when
  pandas is not installed.
- A `.zip` path arrives as `wavu.RoiSet` (ImageJ ROI zip).
- Any other path, such as an OME-Zarr folder, arrives as `pathlib.Path`. The
  script opens it itself.

### `ctx`

| member | meaning |
|---|---|
| `ctx.log(msg)` | A line in Fiji's Log window. `print()` inside `run` does the same. |
| `ctx.progress(frac)` | Fiji's progress bar, from 0.0 to 1.0. |
| `ctx.cancelled()` | True once the user pressed Esc. Check it in loops and return early. |
| `ctx.check_cancelled()` | Raises `wavu.Cancelled` if cancelled. |
| `ctx.tmpdir` | A per-job `Path` for files you return. It is deleted when the worker stops. |
| `ctx.meta[name]` | Metadata of each input: `pixel_um`, `axes`, `title`, and `channel_names` when available. |

### The returned dict

| value | what Fiji does |
|---|---|
| `numpy.ndarray` (≥2-D) | Opens it as an image. bool → 8-bit 0/255. Integers that fit in 0..65535 → 16-bit. Other numbers → 32-bit float. |
| `wavu.Image(array, pixel_um=..., axes="ZYX", channel_names=[...])` | Same as an array, plus calibration and axes. Use `axes` ending in `S` for RGB. |
| pandas `DataFrame` or a list of dicts | Writes a CSV and opens it as a Results table. |
| `wavu.RoiSet(path)` (alias `wavu.Roi`) | Opens the ImageJ RoiSet zip in the ROI Manager. |
| `pathlib.Path` | Prints the path to the Log. |
| `int`/`float`/`str`/`bool`/`None` | Prints `name = value` to the Log. |

Images whose name contains "label" get the glasbey LUT. If an output has the
same width and height as the input and no `pixel_um` of its own, it inherits
the input's calibration. Images up to `inline_limit` bytes (4 MiB by default)
and at most 3-D travel inline. Larger ones go through a TIFF in the job's
temp folder.

Returning `None` counts as `{}`. Raising an exception sends Fiji an error with
the full traceback, which appears in the Log and in an error dialog.

## Testing without Fiji

```python
from wavu.testing import FakeCtx, run_script

def test_blur():
    ctx = FakeCtx()                       # FakeCtx(cancel_after=2) simulates Esc
    out = run_script("script.py", {"image": img}, {"sigma": 2}, ctx=ctx)
    assert ctx.progress_values[-1] == 1.0 and ctx.messages
```

`run_script` applies `PARAMS` defaults and type conversion exactly like the
worker does.

## Running without Fiji

```
pixi run wavu run script.py --in image=cells.tif --param sigma=3 --out results
```

## Packaging for other Fiji users

```
pixi run wavu package <script-dir> --name my-cellpose --menu "My Lab>Cellpose Plus" [--out dist/fiji]
```

This writes:

```
dist/fiji/wavu/scripts/my-cellpose/              script.py, pixi.toml, pixi.lock, README.md, helpers
dist/fiji/scripts/Plugins/My Lab/Cellpose Plus.groovy   menu stub -> runScriptFolder(<Fiji>/wavu/scripts/my-cellpose)
dist/my-cellpose-fiji.zip                        the same tree, ready to unzip into Fiji.app
```

The command needs `pixi.lock`. Tests (`test_*.py`), `.pixi`, `.vscode` and
`.github` are left out. A `wavu` dependency given as a local path is
rejected. **Run Python Script** also lists every installed
`<Fiji>/wavu/scripts/*` folder.
