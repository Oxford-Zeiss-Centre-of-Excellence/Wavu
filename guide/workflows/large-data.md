# Large data: stream analysis

!!! warning "It works, but Fiji and napari are not the place to drive it"
    For **images that fit in memory (roughly 1–2 GB)**, keep using the normal
    interactive path: pick an image, press **OK**, get the result. Nothing on
    this page is needed for that.

    With chunked, streamed processing (OME-Zarr), a Wavu script can work
    through data **up to about 50 GB on a local computer**. But Fiji and
    napari are canvas-based viewers built around data held in memory: during
    a stream they see only a **small preview or the final result**, they stay
    slow while it runs, and they are **not the recommended place to drive
    it**. Beyond about 50 GB, use a batch or HPC pipeline instead (see
    [the end of this page](#when-not-to-do-this-in-fiji-or-napari)).

!!! info "A design pattern, not a built-in feature"
    Everything below is how **you** write **your own script**. Wavu itself
    only passes a path and the parameters to `run`, and returns the path your
    script gives back. Chunking, dask and OME-Zarr are your script's
    business, and its packages live in its own `pixi.toml`.

## The idea in plain words

![A big raw 3-D block on a chopping board is cut by a knife into eight pieces; the pieces go in parallel to four small sub-kitchens, each cooking one piece at a time; the cooked pieces are assembled on one plate into the finished meal, which glows when it is complete.](../assets/img/stream/sub-kitchens.svg){ width="800" }

*The big image is chopped into pieces (the OME-Zarr chunks), and several
sub-kitchens (parallel workers) each cook one piece at a time, so only a few
pieces are in memory at once. The cooked pieces are assembled on one plate
into one meal: the result.*

Back to the restaurant. A wedding has ordered dinner for five hundred
guests. No counter holds all those ingredients, so the kitchen works **in
batches**: it fetches ingredients **crate by crate**, cooks several crates
at once on different stoves, and sends plates out as they are ready. The
waiter brings your table only a **tasting plate**, to show the dish looks
right.

For images, the crates are **chunks**: a big image cut into a grid of small
blocks. Each chunk is saved as **its own small file**, so a program can read
one chunk without touching the rest.

![A large image is cut into a grid of chunks; each chunk is saved as its own small file in an OME-Zarr folder; a reader fetches only the chunks it needs, one file at a time, and the numbers measured on each one fill a results table and a plot.](../assets/img/stream/zarr-chunking.svg){ width="800" }

*A big image becomes a folder of small files, one per chunk. A reader
fetches only the files it needs, one at a time, and what it measures on each
chunk becomes a row of the results table and a bar of the plot.*

## Why OME-Zarr

**OME-Zarr** (also called OME-NGFF, Next-Generation File Format) is an open
format for exactly this:

- **Chunked.** Each chunk is its own file, so reading one region costs
  one region, not the whole image.
- **Multiscale.** The image is also stored at lower resolutions (a
  *pyramid*); a viewer shows the small level first and fetches detail only
  where you zoom.
- **Cloud-friendly.** The same layout works in a folder, on a network share
  or in object storage (S3).
- **Open.** A community standard from OME, read by napari, Fiji and Python.

Compare **one big TIFF**: most programs read it as one file from start to
end, a classic TIFF stops at 4 GB (BigTIFF lifts that), and it is written
in order through **one writer**. Fine for a few gigabytes, painful for
fifty.

## Streaming in the backend

The trick is that the waiter never carries the ingredients. Your script does
not receive pixels; it receives a **path**.

![One OME-Zarr store, data.ome.zarr, with the input group /image on the left and the output group /label on the right; the worker reads one chunk at a time into its small memory box, processes it, writes the result chunk into the matching slot of /label and lets it go; each chunk leaves a tiny results table, and at the end these merge into one assembled table at the right.](../assets/img/stream/stream-loading.svg){ width="800" }

*One store, two groups: left the `/image` group, right the `/label`
group. One chunk at a time goes from `/image` into the small memory box, is
processed, is written into its slot in `/label`, and leaves memory. Each
chunk also leaves a small results table; at the end they merge into one
assembled table.*

Step by step, inside `run`:

1. **Receive a path.** Here a text parameter. (A path sent as an *input*
   that is not a TIFF, CSV or ZIP also arrives unopened, as a
   `pathlib.Path`; see [data on the wire](../model/architecture.md#data-on-the-wire).)
2. **Open it lazily.** `dask.array.from_zarr` knows the shape, type and
   chunk grid, but has read **no pixels** yet.
3. **Process chunk by chunk.** You describe the work on the whole array;
   dask turns it into one small task per chunk.
4. **Write the result next to the input**, not in `ctx.tmpdir`, which is
   deleted when the worker stops.
5. **Return a `Path` and a small preview array.** The path is printed in
   the Log; the preview (well under the 4 MiB inline limit) opens as an
   ordinary image.

## Parallel processing with dask

[dask](https://docs.dask.org/en/stable/array.html) is the kitchen's
head chef: it hands crates to stoves.

![Four workers, drawn as turning wheels, each take a different chunk together with a thin border borrowed from its neighbours, process them at the same time and trim the border; each processed chunk goes back into the output grid, and its numbers become a new row of a growing results table.](../assets/img/stream/parallel-processing.svg){ width="800" }

*Four workers process four chunks at once. Each chunk carries a thin
border from its neighbours (the halo), which is trimmed afterwards. Each
result goes two ways: the processed chunk back into its place in the output
grid (the chunk assembly), and its numbers into a new row of the results
table (the result assembly).*

- **`map_blocks`** runs your function on each chunk on its own: right for
  anything that looks at one pixel at a time, such as a threshold.
- **`map_overlap`** first adds a **halo** of `depth` pixels borrowed from the
  neighbouring chunks, runs your function, then trims the halo off. Filters
  that look at neighbours (Gaussian blur, median, morphology) need it, or
  you get seams at every chunk border. `boundary="reflect"` says what to
  borrow at the image's outer edge. For a Gaussian, `depth` of about
  `4 × sigma` pixels is enough.

```python
import dask.array as da

image = da.from_zarr("D:/data/big.zarr", component="0")   # lazy, nothing read yet
mask = image.map_blocks(lambda block: block > 500, dtype=bool)   # no neighbours needed
```

**Chunk size.** Aim for **tens of MB per chunk** (for example 64 × 512 × 512
`uint16` = 32 MB). Much smaller and dask spends its time on bookkeeping;
much bigger and each stove needs a lot of counter space. Use
`image.rechunk(...)` if the chunks on disk are far off.

**Number of workers.** dask's default scheduler for arrays uses **threads**
in one process; they share memory, so passing chunks around is free. Choose
how many with `dask.config.set(num_workers=4)`. If your function is pure
Python and does not get faster with more threads, try
`scheduler="processes"`.

**Memory rule of thumb.** Peak memory ≈ **workers × chunk size × 3 to 4**
(input, halo, a float copy, output). Four workers on 32 MB chunks need
about half a gigabyte, whatever the size of the whole image.

## The code design

A script folder for streaming is an ordinary Wavu script folder. Add the
packages to its `pixi.toml` (all on conda-forge):

```toml
[dependencies]
dask = ">=2024.1"
zarr = ">=2.16"
ome-zarr = ">=0.9"     # conda-forge `ome-zarr`, imported as ome_zarr
scipy = ">=1.10"
tifffile = ">=2023.1"
```

`script.py`, the skeleton:

```python
"""Smooth a large OME-Zarr image chunk by chunk (Gaussian blur)."""
from pathlib import Path

import dask
import dask.array as da
import numpy as np
from dask.callbacks import Callback
from scipy import ndimage

PARAMS = {
    "store": {"type": "str", "default": "", "label": "Input OME-Zarr folder"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
    "output_format": {"type": "choice", "choices": ["ome-zarr", "tiff"], "default": "ome-zarr"},
}


class WavuProgress(Callback):
    """Report dask's finished tasks as ctx.progress, and stop when the user cancels."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    def _start_state(self, dsk, state):
        self.total = sum(len(state[k]) for k in ("ready", "waiting", "running", "finished"))

    def _posttask(self, key, result, dsk, state, worker_id):
        self.ctx.progress(len(state["finished"]) / max(self.total, 1))
        self.ctx.check_cancelled()          # raises wavu.Cancelled, which stops dask


def run(ctx, inputs, params):
    store = Path(params["store"])
    sigma = params["sigma"]
    image = da.from_zarr(str(store), component="0")    # full resolution, lazy
    ctx.log(f"{image.shape} {image.dtype}, chunks {image.chunksize}")

    depth = int(4 * sigma) + 1                         # the halo a Gaussian needs
    smoothed = image.astype(np.float32).map_overlap(
        ndimage.gaussian_filter, depth=depth, boundary="reflect", sigma=sigma)

    with dask.config.set(scheduler="threads", num_workers=4):
        if params["output_format"] == "ome-zarr":
            out = store.with_name(store.stem + "-smoothed.zarr")
            write_ome_zarr(smoothed, out, ctx)
        else:
            out = store.with_name(store.stem + "-smoothed.tif")
            write_tiff(smoothed, out, ctx)

        z = smoothed.shape[0] // 2                     # preview: middle plane, downsampled
        step = max(1, max(smoothed.shape[1:]) // 512)
        preview = smoothed[z, ::step, ::step].compute()
    return {"result": out, "preview": preview}
```

The two writers. **OME-Zarr** (the default) writes chunk by chunk, in
parallel, and builds the resolution pyramid:

```python
def write_ome_zarr(arr, out, ctx):
    import zarr
    from ome_zarr.io import parse_url
    from ome_zarr.writer import write_image

    root = zarr.group(store=parse_url(str(out), mode="w").store)
    with WavuProgress(ctx):
        write_image(arr, group=root, axes="zyx", storage_options={"chunks": arr.chunksize})
```

**TIFF** goes through **one writer**, plane after plane, so it is slower,
cannot run in parallel, and the result is one big file that most viewers
read as a whole. Here the progress and cancel checks sit in the loop:

```python
def write_tiff(arr, out, ctx):
    import tifffile

    cz = arr.chunksize[0]

    def planes():                                      # one block of planes at a time
        for z0 in range(0, arr.shape[0], cz):
            ctx.check_cancelled()
            ctx.progress(z0 / arr.shape[0])
            yield from arr[z0:z0 + cz].compute()

    tifffile.imwrite(out, planes(), shape=arr.shape, dtype=arr.dtype, bigtiff=True)
```

The skeleton assumes a 3-D `zyx` image whose full-resolution level is `0`,
as in a single-image OME-Zarr. For 4-D or 5-D data, change `axes` and the
preview slice to match.

**Calling it.** The output format is just a parameter, so it is part of
the call and defaults to OME-Zarr:

=== "Groovy (Fiji)"

    ```groovy
    def r = wavu.run(folder, "script",          // folder: the script folder
            [store: "D:/data/big.zarr", output_format: "ome-zarr"], [:])
    println r.files.result          // the path of the new OME-Zarr
    ```

=== "Python"

    ```python
    from wavu.client import Worker

    with Worker.start("path/to/stream-folder", on_log=print) as w:
        res = w.run("script", {"store": "D:/data/big.zarr", "output_format": "ome-zarr"})
        out = res.outputs["result"].value        # a pathlib.Path
        preview = res.outputs["preview"].value   # a small NumPy array
    ```

`store` is a plain text parameter, so it must be a path **the worker** can
see. Wavu translates the paths of inputs for a container, but not text
parameters: for a worker in a container, type the path as the container
sees it.

**Looking at the result.** Open it lazily, so only the visible part is read:
in napari with the [napari-ome-zarr](https://github.com/ome/napari-ome-zarr)
reader (`viewer.open(out, plugin="napari-ome-zarr")`), in Fiji with
**File › Import › HDF5/N5/Zarr/OME-NGFF…** (the N5 plugins). The caveat
from the top still holds: browsing works, analysing the whole thing inside
the viewer does not.

## When not to do this in Fiji or napari

- **Beyond about 50 GB**, many files or many hours: run the same chunked
  code as a **batch job** on a workstation, with no viewer at all
  (`pixi run wavu run script.py --param store=D:/data/big.zarr` in a
  terminal), on an **HPC cluster** (dask's distributed
  scheduler spreads chunks over many machines), or in the **cloud** next to
  data in object storage.
- **When the result must be one TIFF** bigger than memory: possible, but
  slow; prefer OME-Zarr and convert only the part you need.

## In one sentence

For data too large for memory, give your script a **path** instead of
pixels, let dask cook the OME-Zarr chunk by chunk on several stoves, write
the result next to the input and send the viewer only a tasting plate,
while Wavu itself just passes the path in and the path out.
