# Real images

## The idea in plain words

*Blobs* is a single flat picture. Your microscope images are often a **pile
of pictures**: several colour channels, several focal planes (a z-stack),
maybe several time points. Wavu hands your script the **whole pile** as one
NumPy array, and, when the viewer knows, tells you how it is stacked. It is like receiving a box of
slides together with a label saying which way they are sorted.

![A stack of image planes: time, z, channel, then y and x](../assets/img/axes.svg){ width="640" }

## How the array is shaped

=== "Fiji"

    The axes always come in this order, and any axis of length 1 is dropped:

    **T** (time) · **Z** (planes) · **C** (channels) · **Y** · **X**, plus a
    last axis **S** of length 3 for an RGB colour image.

    | Image in Fiji | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | one 2-D grey image, 512 × 512 | `(512, 512)` | `"YX"` |
    | 3 channels | `(3, 512, 512)` | `"CYX"` |
    | z-stack of 20 planes, 2 channels | `(20, 2, 512, 512)` | `"ZCYX"` |
    | an RGB photo | `(512, 512, 3)` | `"YXS"` |

    So "channel 2 of every plane" is `img[:, 1]` for a `ZCYX` image. Fiji
    sends 8-bit, 16-bit, 32-bit or RGB pixels unchanged.

=== "napari"

    You get the chosen layer's data as it is, in the layer's own axis
    order: a z-stack layer arrives as `(20, 512, 512)`. napari usually
    opens each channel as its own layer, so pick the channel you want.

    | Layer in napari | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | one 2-D grey image | `(512, 512)` | `"YX"` |
    | a z-stack of 20 planes | `(20, 512, 512)` | `"ZYX"` if the layer's axis labels say z, y, x; otherwise not set |
    | an RGB photo | `(512, 512, 3)` | `"YXS"` |

    A **multiscale** layer (an image pyramid) sends its full-resolution
    level. 2-D and RGB layers always come with axis letters; bigger layers
    only when napari's axis labels are plain letters (t, z, c, y, x), as
    OME-Zarr readers set them. So read the axes with `.get("axes")` and look
    at `img.ndim` and `img.shape`.

## What else you get: `ctx.meta`

`ctx.meta["image"]` holds what the viewer knows about the image chosen for
the `"image"` field:

- `"axes"`: the axis letters, as above (always in Fiji; in napari for 2-D
  and RGB layers, and for bigger layers whose axis labels are t/z/c/y/x);
- `"pixel_um"`: the pixel size in micrometres, if known: from the image's
  calibration in Fiji, from the layer's **scale** in napari (when its last
  two values are equal and not 1);
- `"title"`: the window title (Fiji) or the layer name (napari).

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # None if the viewer did not say
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

Checking the shape and raising a clear `ValueError` is kinder than letting
your code crash later: Fiji shows the sentence in an error window, napari in
the panel's log and a notification.

## How big is too big?

Wavu is built for **interactive work on one image that fits comfortably in
memory**, roughly up to **1–2 GB**. Small images travel in a single message;
bigger ones are passed through a temporary TIFF file on your disk. You do
not have to do anything: `inputs["image"]` is a NumPy array either way.
The limit is the same in Fiji and napari.

!!! warning "napari: big lazy layers are loaded in full"
    napari can show huge images lazily (a *dask* array), reading only the
    part on screen. Wavu cannot: it loads the whole layer into memory before
    sending it, so pick a layer that fits in memory (a crop, one channel,
    or a lower-resolution copy).

Beyond that size, or for hundreds of files, Wavu is the wrong tool. Convert
to OME-Zarr and use a batch or HPC workflow instead.

## Slow first runs (and how to keep users calm)

Two things can make a *first* run slow, and both happen only once:

1. **The environment is built.** pixi downloads the packages listed in
   `pixi.toml`. With PyTorch (needed by Cellpose) that can be **1–2 GB**
   and several minutes. Fiji's Log or the napari panel's log says so while
   it happens.
2. **Model weights are downloaded.** Tools such as Cellpose fetch their
   trained model from the internet the first time it is used. This happens
   *inside your script*, so the viewer knows nothing about it and may look
   frozen.

**Always log before a slow step**, so the user knows what is going on:

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "A working Cellpose setup"
    The Wavu repository has a complete Cellpose nuclei script, including a
    `pixi.toml` with PyTorch, Cellpose and an optional NVIDIA GPU setup:
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei).
    Copy its `[dependencies]` and `[pypi-dependencies]` lines into your own
    `pixi.toml`. Apple-silicon Macs use their GPU out of the box.

## In one sentence

Your script gets the whole image as one array (in **T Z C Y X** order from
Fiji, in the layer's own order from napari; read `ctx.meta` and the shape
to be sure), it should stay below about 1–2 GB in either viewer, and you should
`ctx.log` before anything slow, such as a first model download.

[Next: share as a container :material-arrow-right:](container.md){ .md-button }
