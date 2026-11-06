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

??? tip "Axis order: T C Z Y X recommended (storage, transport, compute)"

    Wavu does not reorder anything: Fiji sends **T Z C Y X** (ImageJ's
    hyperstack order), napari sends the layer's own order, and Fiji expects
    results back in its order. Inside your script you are free to choose.
    We recommend **T C Z Y X**; here are the choices per layer:

    | layer | recommended | alternatives | pick the alternative when |
    |---|---|---|---|
    | **Storage** (files on disk) | OME-Zarr in **T C Z Y X** (or C Z Y X, Z Y X) | ImageJ TIFF in **T Z C Y X** | small data you mostly open in Fiji (an ImageJ TIFF can only store its own order) |
    | **Transport** (Wavu ↔ your script) | convert to **T C Z Y X**, C-contiguous, at the start of `run()`; convert back before returning | keep what Wavu gives (**T Z C Y X** from Fiji) | plane-by-plane processing (filters, thresholds) where the order does not matter |
    | **Compute** (NumPy, PyTorch, GPU) | **T C Z Y X**: one time point is `(C, Z, Y, X)`, PyTorch's `(N, C, D, H, W)` with a batch axis | **channels last** (B Z Y X C) in GPU memory only: `tensor.to(memory_format=torch.channels_last_3d)`; TensorFlow/Keras default to it | mixed-precision 3-D convolutions on recent NVIDIA GPUs; Keras models |

    Why T C Z Y X? Four things pull on the axis order, and it serves all of
    them:

    1. **The microscope.** The camera reads out one **Y × X** frame at a
       time (fastest), a piezo stage moves in **Z**, filters or lasers switch
       **C**, and the time interval **T** is the slowest. Keeping Y, X
       innermost, next to Z, follows how the data is acquired and keeps the
       3-D volume together. (The exact Z/C loop order varies between set-ups.)
    2. **Storage and chunks.** NumPy and Zarr arrays are *C-contiguous*: the
       last axis changes fastest. With T C Z Y X, a chunk such as
       `(1, 1, 64, 512, 512)` is one compact 3-D block of **one channel**, so
       reading only channel 0 (say DAPI) reads only those files; with
       interleaved channels, every read fetches all channels. The
       [OME-NGFF specification](https://ngff.openmicroscopy.org/0.4/#axes-md)
       therefore requires time first, then channel, then space (versions 0.4
       and 0.5; a proposal to loosen this,
       [RFC-3](https://ngff.openmicroscopy.org/rfc/3/index.html), is still
       under review). Fiji, napari and Bio-Formats all read it. Data on disk
       is kept for decades; GPUs change every few years.
    3. **Deep learning.** `(C, Z, Y, X)` plus a batch axis is exactly what
       [PyTorch's `Conv3d`](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv3d.html)
       expects, `(N, C, D, H, W)`. `torch.from_numpy()` of a C-contiguous
       array shares its memory: nothing is copied.
    4. **The GPU.** NVIDIA Tensor Cores can run mixed-precision (FP16/BF16)
       3-D convolutions faster with the channels innermost ("channels
       last"). Convert **only inside GPU memory**, right before the heavy
       layers; the shape stays `(N, C, D, H, W)`, only the strides change.
       Make results contiguous again (`.contiguous()`) before they leave the
       GPU. The chip's preference never reaches the files.

    Converting in and back, in your script:

    ```python
    import numpy as np
    import wavu

    def to_tczyx(img, axes):
        """Reorder to T, C, Z, Y, X (only the axes present). Returns (array, new axes)."""
        new = "".join(a for a in "TCZYX" if a in axes)
        return np.ascontiguousarray(np.transpose(img, [axes.index(a) for a in new])), new

    def back(arr, axes_now, axes_wanted):
        """Reorder a result back, e.g. to the input's own order before returning it."""
        return np.ascontiguousarray(np.transpose(arr, [axes_now.index(a) for a in axes_wanted]))

    def run(ctx, inputs, params):
        axes = ctx.meta["image"].get("axes") or "YX"    # from Fiji e.g. "TZCYX" or "ZCYX"
        x, ours = to_tczyx(inputs["image"], axes)       # e.g. (C, Z, Y, X), "CZYX"
        # PyTorch: one time point with a batch axis, no copy
        #   batch = torch.from_numpy(x)[None]           # (1, C, Z, Y, X) for "CZYX"
        y = x * 2                                       # your computation, same layout out
        return {"result": wavu.Image(back(y, ours, axes), axes=axes)}
    ```

    (RGB images, axes ending in `S`, are left out here: convert them to grey
    or split the colours first. If a napari layer arrives without `axes`,
    you know its order best: pass the letters yourself.)

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

Beyond that size, convert to OME-Zarr and let the script read it piece by
piece: [stream analysis](../workflows/large-data.md) handles up to about
50 GB on a local computer. It works, but it is not recommended to drive it
from Fiji or napari. For hundreds of files, see
[batch processing](../workflows/batch.md); beyond about 50 GB, use a batch
or HPC workflow.

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
to be sure; we recommend reordering to **T C Z Y X**, the OME-NGFF and PyTorch
order), it should stay below about 1–2 GB in either viewer, and you should
`ctx.log` before anything slow, such as a first model download.

[Next: share as a container :material-arrow-right:](container.md){ .md-button }
