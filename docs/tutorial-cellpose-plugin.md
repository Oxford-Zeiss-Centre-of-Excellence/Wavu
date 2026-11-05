# Tutorial: "I have a brilliant Cellpose algorithm, and I want everyone to use it in Fiji"

This guide takes you from a Python idea to a Fiji menu item that anyone can install with one tick in Fiji's updater. It also covers testing, VS Code debugging, and automated releases to GitHub, PyPI and an ImageJ update site.

**Who this is for:** you know some Python, and you have used Fiji. You do **not** need Java, Groovy, conda or Docker.

**What you will build:** *Plugins › My Lab › Cellpose Plus*. It runs Cellpose nuclei segmentation plus your own post-processing, then returns a label image, the outlines in the ROI Manager, and a results table.

```
 Fiji (menu + dialog)  ──HTTP on localhost──▶  Wavu worker  ──▶  your script.py
        ▲                                     (runs in YOUR pixi env:
        └──── images, ROIs, tables ◀──────────  cellpose, torch, ...)
```

Your script runs in its **own** environment. Its packages can never clash with Fiji, with other Wavu scripts or with your system Python.

> **Scope:** Wavu is for interactive work on images that fit in memory (up to roughly 1–2 GB). For very large data, use a batch/HPC pipeline instead.

---

## 0. What you need (once)

| Tool | Why | Install |
|---|---|---|
| **pixi** | environments | Windows: `powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 \| iex"`; macOS/Linux: `curl -fsSL https://pixi.sh/install.sh \| sh` |
| **git** + a **GitHub** account | code and releases | <https://git-scm.com> |
| **Fiji** | to try it | <https://fiji.sc> |
| VS Code + Python extension *(optional)* | debugging | <https://code.visualstudio.com> |

**Install Wavu into Fiji:**
1. Until the Wavu update site is live, download `wavu-fiji-<version>.zip` from the [Wavu releases](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/releases).
2. Unzip it **into your `Fiji.app` folder**, so the files merge into `Fiji.app/scripts/Plugins/Wavu/`.
3. Restart Fiji. A **Plugins › Wavu** menu should now appear.
4. Run **Plugins › Wavu › Setup Python (pixi)** once. If Fiji can't find pixi, this downloads it.

*Later, once the update site is live, steps 1–2 become: **Help › Update… › Manage update sites**, tick **Wavu**, restart.*

---

## 1. Create your project from the template

```bash
git clone https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu.git
cd Wavu
pixi run new-script my-cellpose --dest ..   # copies templates/wavu-script next to the Wavu clone;
                                           # its pixi.toml gets wavu from GitHub (a release tag once one exists)
cd ../my-cellpose
git init -b main
```

You now have:

```
my-cellpose/
├── script.py              # your algorithm: PARAMS + run()
├── test_script.py         # pytest tests (no Fiji needed)
├── pixi.toml              # this script's own environment (pixi.lock appears after the first install)
├── .vscode/launch.json    # "Attach to Wavu worker"
├── .github/workflows/release.yml   # tag -> GitHub Release (+ optional PyPI, update site)
└── README.md
```

Try the example (a Gaussian blur) straight away:

```bash
pixi run test          # first run installs the environment and creates pixi.lock; the tests pass
```

(pixi fetches `wavu` from GitHub with `git`, which is why git is on the list in step 0.)

---

## 2. Add your dependencies

```bash
pixi add "python=3.11" pytorch "numpy<2.3" roifile tifffile scikit-image pandas
pixi add --pypi "cellpose>=3.1,<4"
```

- This updates `pixi.toml` **and** `pixi.lock`. Commit both: the lock file is what guarantees every user gets exactly your environment.
- **GPU (optional):** copy the `[feature.cuda]` and `[environments]` blocks from `examples/cellpose_nuclei/pixi.toml` in the Wavu repo. CPU is the default. Apple-silicon GPUs (MPS) work out of the box.

---

## 3. Write the algorithm: `PARAMS` + `run()`

A Wavu script is a plain Python module with two things:

- **`PARAMS`**: the dialog fields. Fiji builds the dialog from this dict, so you write no UI code.
  - Types: `float`, `int`, `str`, `bool`, `choice` (needs `"choices"`), and `image`, which lets the user pick an open Fiji image.
- **`run(ctx, inputs, params) -> dict`**:
  - `inputs` contains numpy arrays for every `image` parameter.
  - `params` contains the other values, with defaults filled in.
  - `ctx.log(msg)` writes to Fiji's Log.
  - `ctx.progress(0..1)` drives Fiji's progress bar.
  - `ctx.cancelled()` becomes true when the user presses **Esc** in Fiji.
  - `ctx.tmpdir` is a scratch folder for this run.

Replace `script.py` with your algorithm:

```python
"""Cellpose Plus: Cellpose nuclei + my size/shape clean-up."""
from pathlib import Path
import numpy as np
import wavu

PARAMS = {
    "image":     {"type": "image", "label": "Nuclei image (2-D)"},
    "diameter":  {"type": "float", "default": 0.0, "label": "Nucleus diameter, px (0 = auto)"},
    "min_area":  {"type": "int",   "default": 30,  "label": "Drop objects smaller than (px)"},
    "use_gpu":   {"type": "bool",  "default": True, "label": "Use GPU if available"},
}

def run(ctx, inputs, params):
    import roifile
    from cellpose import models, utils
    import pandas as pd
    from skimage.measure import regionprops_table

    img = np.asarray(inputs["image"])
    if img.ndim != 2:
        raise ValueError(f"need one 2-D channel, got {img.shape}; pick a single channel/plane in Fiji")

    ctx.log("Loading Cellpose nuclei model"); ctx.progress(0.1)
    model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
    if ctx.cancelled():
        return {}

    masks, *_ = model.eval(img, diameter=params["diameter"] or None, channels=[0, 0])
    ctx.progress(0.8)

    # --- your brilliant part: remove tiny fragments, relabel 1..N ---------------
    ids, areas = np.unique(masks[masks > 0], return_counts=True)
    keep = ids[areas >= params["min_area"]]
    lut = np.zeros(masks.max() + 1, dtype=np.uint16); lut[keep] = np.arange(1, len(keep) + 1)
    labels = lut[masks]
    ctx.log(f"{len(keep)} nuclei kept ({len(ids) - len(keep)} small fragments removed)")

    # --- outputs: each one opens in Fiji automatically --------------------------
    table = pd.DataFrame(regionprops_table(labels, img, properties=("label", "area", "centroid", "mean_intensity")))
    rois = [roifile.ImagejRoi.frompoints(o) for o in utils.outlines_list(labels) if len(o) >= 3]
    roi_zip = Path(ctx.tmpdir) / "nuclei_RoiSet.zip"
    roifile.roiwrite(roi_zip, rois)
    ctx.progress(1.0)
    return {
        "labels": labels,                 # numpy array  -> new image window
        "nuclei": table,                  # DataFrame (or list of dicts) -> results table
        "outlines": wavu.RoiSet(roi_zip), # ImageJ RoiSet -> ROI Manager
    }
```

**Rules of thumb:**
- Import heavy packages **inside** `run()`. Fiji can then list your script and show its dialog instantly.
- Raise `ValueError` with a plain sentence for user mistakes. Fiji shows the message as-is.
- Check `ctx.cancelled()` between long steps.

---

## 4. Test it without Fiji (do this first, every time)

`wavu.testing` gives you a fake `ctx`, so tests run in plain pytest:

```python
# test_script.py
from pathlib import Path
import numpy as np, pytest
from wavu.testing import FakeCtx, run_script

SCRIPT = Path(__file__).with_name("script.py")

def blobs():
    yy, xx = np.mgrid[:128, :128]
    img = np.zeros((128, 128), np.float32)
    for cy, cx in [(30, 30), (30, 90), (90, 60)]:
        img += 200 * np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * 6 ** 2))
    return img

def test_finds_three_nuclei():
    ctx = FakeCtx()
    out = run_script(SCRIPT, {"image": blobs()}, {"diameter": 15, "use_gpu": False}, ctx=ctx)
    assert out["labels"].max() == 3
    assert ctx.progress_values[-1] == 1.0

def test_rejects_stacks():
    with pytest.raises(ValueError, match="2-D"):
        run_script(SCRIPT, {"image": np.zeros((2, 8, 8))}, {})
```

```bash
pixi run test
```

**Real test data:** Wavu's own tests use one frame from the Cell Tracking Challenge (2-D fluorescent nuclei), downloaded on demand by `pixi run fetch-test-data` in the Wavu repo. The data is **not** redistributed; see `docs/test-data.md` for its licence and citation. You can use the same frame to test against its ground-truth segmentation, e.g. assert F1 > 0.8.

---

## 5. Try it in Fiji

1. Open a nuclei image, e.g. the CTC frame or **File › Open Samples › Blobs**.
2. Start **Plugins › Wavu › Run Python Script…** and choose your `my-cellpose` folder.
3. The first start builds your environment from `pixi.lock`. That's a one-off download, about 1–2 GB with PyTorch, and the Log shows progress. Later starts are fast.
4. Fill in the dialog (a script picker appears first only if the folder has several scripts), click **OK**. Press **Esc** to cancel. Log lines and the progress bar update live.
5. The label image, the results table and the ROI Manager outlines appear.

---

## 6. Debug in VS Code (breakpoints in your script, live from Fiji)

1. In a terminal in `my-cellpose/`, run `pixi run debug`. This starts the worker with debugpy on port 5678 and writes its address to `~/.wavu/worker.json`.
2. In VS Code, open the folder, set a breakpoint in `run()`, and start **Run › Start Debugging › "Attach to Wavu worker"**.
3. In Fiji, run **Plugins › Wavu › Connect to Running Worker** (accept the default handshake file), then **Run Python Script…** and pick the *running:* entry for your folder.
4. VS Code stops at your breakpoint, where you can inspect `img`, `masks`, and so on.

When you're done, use **Plugins › Wavu › Stop Worker** (this also shuts down the terminal worker), or press Ctrl+C in the terminal.

*Alternative:* tick **Debug in VS Code** in the script's Fiji dialog. Fiji then restarts the worker with debugpy and waits until VS Code attaches.

---

## 7. Package it as a Fiji menu item

```bash
pixi install            # makes sure pixi.lock exists; `wavu package` refuses to run without it
pixi run wavu package . --name my-cellpose --menu "My Lab>Cellpose Plus"
```

This creates `dist/fiji/`, laid out exactly like a Fiji installation, plus `dist/my-cellpose-fiji.zip`:

```
dist/fiji/
├── wavu/scripts/my-cellpose/         script.py, pixi.toml, pixi.lock, README.md
└── scripts/Plugins/My Lab/Cellpose Plus.groovy    # ~10-line menu stub calling Wavu
```

**Test it locally:** unzip `dist/my-cellpose-fiji.zip` into `Fiji.app` and restart. **Plugins › My Lab › Cellpose Plus** now runs your script directly, with no folder picking. The first start installs exactly the environment in your `pixi.lock` (`pixi run --frozen`), and the Log says it is downloading packages. Installed scripts also show up in **Plugins › Wavu › Run Python Script…** as *installed: my-cellpose*.

---

## 8. Deliver it

Everything below is automated by `.github/workflows/release.yml`, which came with the template. You set things up once; after that, each release is just **push a tag**.

### 8a. GitHub: the source and the release zip

```bash
gh repo create my-lab/my-cellpose --public --source . --push
```

Release by tagging:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow then:
1. runs `pixi run test`;
2. runs `wavu package`;
3. creates a **GitHub Release** with `my-cellpose-fiji.zip` attached.

Users can already install from that zip, as in step 7.

*Tip:* write commit messages as `feat: …` / `fix: …` (Conventional Commits). The release notes are then generated from them.

### 8b. PyPI: share the algorithm itself (optional)

Do this if your algorithm is also useful **without** Fiji, e.g. in napari or notebooks:
1. Move the core logic into a small package, `src/cellpose_plus/`, with a `pyproject.toml`.
2. Make `script.py` a thin wrapper that calls it.
3. Create a [pypi.org](https://pypi.org) account. A lab can register a PyPI *organisation*.
4. Add a **Trusted Publisher** under PyPI › Your projects › Publishing › Add a pending publisher, with:
   - owner = your GitHub user/org;
   - repo = `my-cellpose`;
   - workflow = `release.yml`;
   - environment = `pypi`.

   This means no passwords or tokens are stored anywhere.
5. In GitHub, go to *Settings › Secrets and variables › Actions › Variables* and add `PYPI_PUBLISH = true`.

The next tag also publishes `cellpose-plus` to PyPI. Others can then `pixi add --pypi cellpose-plus` or `pip install cellpose-plus`.

### 8c. ImageJ update site: one-tick install for every Fiji user

1. **Create an ImageJ wiki account** at <https://imagej.net> (*Log in › Create account*).
2. **Create your personal update site** in Fiji: *Help › Update… › Manage update sites › Add Unlisted Site*. Then follow <https://imagej.net/update-sites/setup>. You get `https://sites.imagej.net/<YourName>/` and an upload password.
3. **Store the credentials for CI** in GitHub, under *Settings › Secrets and variables › Actions*:
   - **Secrets:** `UPDATE_SITE_NAME` (e.g. `MyLab`), `UPDATE_SITE_USER` (your wiki user), `UPDATE_SITE_PASS` (the upload password).
   - **Variable:** `FIJI_UPDATE_SITE = true`.
4. **Push a tag.** The workflow uploads `dist/fiji/` to your update site with the Fiji updater command line (`--update edit-update-site` then `--update upload-complete-site`).

   > **Not yet verified:** whether the Fiji updater uploads the top-level `wavu/` folder (see Wavu's `docs/decisions.md` D13). Check the first upload in a clean Fiji before announcing the site.
5. **Make it discoverable:** add your site to the [list of update sites](https://imagej.net/list-of-update-sites/) with a one-line description, and say that it **requires the Wavu update site**.

**What your users do:**
1. Go to *Help › Update… › Manage update sites*.
2. Tick **Wavu** and **MyLab**.
3. Restart Fiji.
4. Run **Plugins › My Lab › Cellpose Plus**. The first run sets up Python by itself.

That's it: no Python, conda or terminal for your users.

### 8d. Container (optional, for HPC or reproducibility)

Wavu publishes a worker image (`ghcr.io/oxford-zeiss-centre-of-excellence/wavu-worker`). To ship your own script as a container, see *Launch modes* in the Wavu README.

---

## 9. Keeping it alive with minimal effort

- **Pin with the lock file, and update on purpose:** `pixi update && pixi run test`, then commit `pixi.lock` and tag a patch release.
- **Licence:** pick one before your first release and add a `LICENSE` file. Cellpose is BSD-3-Clause; check the licence of any model weights you ship or download.
- **Credit:** add a `CITATION.cff`, and connect the repo to Zenodo for a DOI on every release.
- **Support:** point users to the [image.sc forum](https://forum.image.sc) with a tag for your tool, not to your inbox.

---

### Reference: the script contract at a glance

| Piece | Type | Notes |
|---|---|---|
| `PARAMS[name]["type"]` | `float` `int` `str` `bool` `choice` `image` | `choice` needs `"choices": [...]`; `image` = an open Fiji image |
| `run(ctx, inputs, params)` | function | must return a `dict` |
| return: numpy array | image | opens as a new Fiji image (labels: integer dtype) |
| return: DataFrame / list of dicts | table | opens as a results table |
| return: `wavu.RoiSet(path)` | ROIs | loads into the ROI Manager |
| return: number / str | value | printed to the Log |
| `ctx.log` / `ctx.progress` / `ctx.cancelled()` / `ctx.tmpdir` | | live in Fiji |

Full details are in [script-contract.md](script-contract.md).
