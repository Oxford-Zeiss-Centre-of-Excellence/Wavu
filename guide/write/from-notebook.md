# From notebook to Wavu

## The idea in plain words

A notebook cell and a Wavu script do the same work; only the **doors in and
out** change. In a notebook *you* type the settings, load the file and look
at the plot. In Wavu, **Fiji** fills in the settings from a dialog, hands
over the image that is already open, and shows whatever you return. Your
analysis in the middle stays the same.

```mermaid
flowchart LR
    subgraph NB["Notebook"]
        A1["sigma = 2.0"]:::script
        A2["img = io.imread(...)"]:::script
        A3["your analysis"]:::worker
        A4["plt.imshow(labels)"]:::script
    end
    subgraph WV["Wavu script"]
        B1["PARAMS → dialog"]:::fiji
        B2["inputs['image']"]:::fiji
        B3["your analysis"]:::worker
        B4["return {'labels': labels}"]:::fiji
    end
    A1 -.-> B1
    A2 -.-> B2
    A3 -.-> B3
    A4 -.-> B4

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## The translation table

| In your notebook | In `script.py` | What you see in Fiji |
|---|---|---|
| `sigma = 2.0` | `"sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"}` in `PARAMS`, then `params["sigma"]` | a number field **Sigma (pixels)** |
| `img = io.imread("cells.tif")` | `"image": {"type": "image"}` in `PARAMS`, then `inputs["image"]` | a drop-down of the open images |
| `print("found", n)` | `ctx.log(f"found {n}")` (`print` also works) | a line in the **Log** window |
| `plt.imshow(labels)` | `return {"labels": labels}` | a new image window called *…-labels* |
| `df` (a table) | `return {"cells": df}` | a Results table |

## A worked example

Here is a typical notebook cell that thresholds nuclei and counts them:

```python
from skimage import io, filters, measure

sigma = 2.0
img = io.imread("nuclei.tif")
smooth = filters.gaussian(img, sigma)
mask = smooth > filters.threshold_otsu(smooth)
labels = measure.label(mask)
print("found", labels.max(), "nuclei")
plt.imshow(labels)
```

And the same thing as a Wavu script. Replace the contents of `script.py` with:

```python
"""Count nuclei -- Otsu threshold after a Gaussian blur."""

PARAMS = {
    "image": {"type": "image", "label": "Nuclei image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
}


def run(ctx, inputs, params):
    from skimage import filters, measure

    img = inputs["image"]                     # the image chosen in the dialog
    smooth = filters.gaussian(img, params["sigma"])
    mask = smooth > filters.threshold_otsu(smooth)
    labels = measure.label(mask)
    ctx.log(f"found {labels.max()} nuclei")   # appears in Fiji's Log
    return {"labels": labels}                 # opens as a new image
```

This uses scikit-image, so add `scikit-image = "*"` to `pixi.toml` first
([how](get-the-template.md#adding-a-package)). Save both files,
**Stop Worker**, and run it on *Blobs*.

## The three rules

1. **`PARAMS` at the top** is the dialog. Every entry becomes one field.
2. **`def run(ctx, inputs, params):`** is where the work happens. Images
   arrive in `inputs`, the other settings in `params`, and `ctx` is your
   line back to Fiji (Log, progress bar, cancel).
3. **Return a dictionary.** Each key becomes the name of a result
   (Fiji adds the image's name in front, as in *blobs-labels*), each value
   is shown in the right way.

!!! tip "Two habits that save time"
    - **Import heavy packages inside `run`**, as above. Fiji can then show the
      dialog at once, without waiting for big imports.
    - **Raise a plain-English error** for user mistakes, for example
      `raise ValueError("Please pick a single-channel image")`. Fiji shows
      the message in an error window.

The first line of the docstring (the text in triple quotes at the very top)
appears at the top of the dialog, so make it a short description.

## In one sentence

Keep your analysis as it is; just take settings from `params`, the image from
`inputs`, write messages with `ctx.log`, and `return` what you want to see.

[Next: PARAMS = your dialog :material-arrow-right:](params.md){ .md-button }
