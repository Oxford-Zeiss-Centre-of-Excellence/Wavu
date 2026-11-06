# PARAMS = your dialog

## The idea in plain words

`PARAMS` is the **menu card** your waiter hands to the customer. You list
what can be chosen, and the viewer draws the fields for you: Fiji as a
dialog, napari as a form in the Wavu panel. No buttons or windows to program,
and the same `PARAMS` works in both. Each entry has a **name** (what your code uses), a **type** (what
kind of field), a **default** (what is filled in at first) and an optional
**label** (the text the user reads).

```mermaid
flowchart LR
    P["PARAMS entry<br/>&quot;sigma&quot;: {type: float,<br/>default: 2.0,<br/>label: Sigma (pixels)}"]:::script
    D["Dialog / form field<br/>Sigma (pixels) [2.000]"]:::fiji
    R["In run():<br/>params[&quot;sigma&quot;] == 2.0"]:::worker
    P --> D --> R

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## Every field type in one example

```python
"""Field types demo -- one of each."""

PARAMS = {
    "image":  {"type": "image", "label": "Nuclei image"},
    "sigma":  {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
    "n":      {"type": "int",   "default": 3},
    "name":   {"type": "str",   "default": "cells"},
    "fast":   {"type": "bool",  "default": True},
    "method": {"type": "choice", "choices": ["otsu", "li"], "default": "otsu"},
}
```

Each viewer turns that into its own fields; your code gets the same values:

| `type` | Field in Fiji | Field in napari | What `run` receives |
|---|---|---|---|
| `float` | number box (3 decimals) | number box with decimals | a decimal number, e.g. `2.0`, in `params` |
| `int` | number box (no decimals) | whole-number box | a whole number, e.g. `3`, in `params` |
| `str` | text box | text box | text, e.g. `"cells"`, in `params` |
| `bool` | checkbox | checkbox | `True` or `False`, in `params` |
| `choice` | drop-down | drop-down | the chosen text, e.g. `"otsu"`, in `params` |
| `image` | drop-down of the **open images** | drop-down of the **Image and Labels layers** | a NumPy array in **`inputs`** (not `params`) |

napari's drop-down of layers updates by itself when you add or remove a
layer.

## The small print

- **`default` is required** for every type except `image`. For `choice` it
  may be left out; the first item is used.
- **`choices`** is required for `choice`: a list of the options.
- **`label` is optional.** Without it, both viewers show the name with the
  first letter capitalised and `_` turned into spaces: `min_area` becomes
  *Min area*.
- **Names** must be valid Python names: letters, digits and `_`, not
  starting with a digit.
- **The values are checked** before your code runs. A wrong type or an
  unknown option is refused with a message, so `run` always gets clean
  values of the declared type.
- The **first line of the docstring** at the top of `script.py` is shown at
  the top of Fiji's dialog and in the napari panel.
- Fiji's dialog adds one extra checkbox, **Debug in VS Code**, for
  [debugging](../help/debug-in-vscode.md). Leave it off normally.

!!! info "An `image` field needs an open image"
    If your script has an `image` field and nothing is open, Wavu stops
    with a message: in Fiji *"… needs an image -- open one first"*, in
    napari *"…: open an image layer first"*. Open one and run again.

## Two images? Two fields

Want a nuclei image *and* a cytoplasm image? Add two `image` entries. Each
becomes its own drop-down, and each arrives in `inputs` under its own name:

```python
PARAMS = {
    "nuclei": {"type": "image", "label": "Nuclei"},
    "cyto":   {"type": "image", "label": "Cytoplasm"},
}

def run(ctx, inputs, params):
    nuc, cyto = inputs["nuclei"], inputs["cyto"]
    ...
```

## Tables, ROIs, tracks and files: from a script

The dialog only offers images. Everything else (a Results table, the ROI
Manager's outlines, TrackMate's or napari's tracks, napari Points or Shapes,
an OME-Zarr folder) reaches your script when it is **called from another
script**, as in a [pipeline](../workflows/index.md). Such inputs need **no
`PARAMS` entry**: the script reads them from `inputs` by name. Say in the
docstring which names it expects.

| you pass | the script gets in `inputs` |
|---|---|
| an image (`ImagePlus`, NumPy array) | NumPy array |
| a table (`ResultsTable`, a macro table, a pandas DataFrame, a list of dicts) | pandas DataFrame (sent as CSV) |
| a `.zip` of ImageJ ROIs (saved from the ROI Manager, or written from napari Shapes) | `wavu.RoiSet` (read it with `roifile`) |
| any other path (`.csv`, `.tif`, an OME-Zarr folder) | the file loaded, or a `pathlib.Path` for folders |

Tracks travel as a table: one row per spot, with a track id, the frame and
the position.

=== "Groovy (Fiji)"

    ```groovy
    def rm = wavu.roiManager()                               // the ROI Manager you see
    def zip = new File(IJ.getDirectory("temp"), "rois.zip")
    rm.deselect(); rm.runCommand("Save", zip.path)           // all ROIs -> one zip
    Map r = wavu.run(folder, "script", [min_area: 30],
                     [image: imp, rois: zip, spots: ResultsTable.getResultsTable()])
    ```

=== "ImageJ macro"

    A macro passes tables by window title with `tables=`. For ROIs, save the
    zip and give its path as a text field (`"type": "str"`) of the script;
    keep that path free of spaces:

    ```javascript
    zip = replace(getDirectory("temp"), "\\", "/") + "rois.zip";
    roiManager("Save", zip);
    run("Run Script (Macro)", "folder=[D:/scripts/measure] script=script " +
        "params=[rois_zip=" + zip + "] tables=[spots=Results]");
    ```

    The script then reads `params["rois_zip"]` with `roifile.roiread(...)`.

=== "Python (napari)"

    ```python
    import pandas as pd
    import roifile

    pts, trk, shp = viewer.layers["spots"], viewer.layers["tracks"], viewer.layers["cells"]
    points = pd.concat([pd.DataFrame(pts.data, columns=["frame", "y", "x"]), pts.features], axis=1)
    tracks = pd.DataFrame(trk.data, columns=["track_id", "frame", "y", "x"])
    roifile.roiwrite("rois.zip", [roifile.ImagejRoi.frompoints(s[:, -2:][:, ::-1])   # (y, x) -> (x, y)
                                  for s in shp.data])

    with Worker.start("D:/scripts/measure") as w:
        res = w.run("script", {"min_area": 30},
                    {"image": viewer.layers["nuclei"].data, "points": points,
                     "tracks": tracks, "rois": "rois.zip"})
    ```

In the script:

```python
"""Measure inside ROIs. Inputs: image, rois (ROI zip), tracks (table)."""
import roifile

def run(ctx, inputs, params):
    img = inputs["image"]
    tracks = inputs["tracks"]                               # DataFrame
    rois = roifile.roiread(inputs["rois"].path)             # outlines; .coordinates() is (x, y)
    ...
```

## In one sentence

Write one `PARAMS` line per setting, with a type and a default, and Fiji or
napari builds the fields and hands you the checked values in `params`
(images in `inputs`, and tables, ROIs and files too when another script
calls yours).

[Next: what you can return :material-arrow-right:](outputs.md){ .md-button }
