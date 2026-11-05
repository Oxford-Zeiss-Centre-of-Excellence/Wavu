# Wavu

*Wavu* is Fijian for "bridge". It is a bridge from [Fiji](https://fiji.sc) to
Python. You write a short Python script, Fiji shows a dialog for its
parameters, and the script runs in **its own isolated [pixi](https://pixi.sh)
environment**. Logs and progress stream back into Fiji, the results open as
images, tables or ROIs, and you can set breakpoints in VS Code.

```
Fiji (Groovy client, no Java build)  --HTTP/JSON on 127.0.0.1, token-->  wavu-worker (Python, stdlib server)
   dialog from PARAMS, Log, progress                                       runs run(ctx, inputs, params)
                                                                           inside the script folder's pixi env
```

## Who it is for, and the scope

Wavu is for **entry-level Python users** who want to call a Python tool such
as Cellpose, scikit-image or their own code from Fiji. Each script keeps its
own dependencies, so a PyTorch script and a NumPy-2-only script never fight.

**Small, interactive data only.** One image at a time that fits comfortably in
RAM, roughly up to 1-2 GB. Images travel as base64 JSON when small, or as a
temporary TIFF otherwise. **Wavu is not the tool for large data.** For big
volumes, many files or anything that does not fit in memory, convert to
OME-Zarr and use a chunked batch or HPC workflow. Wavu does not try to be that.

The environments isolate *dependencies*. They are **not a security sandbox**.
A script can do anything your user account can do, so run only scripts you
trust.

## Install (interim: release zip)

The Fiji update site "Wavu" is **coming soon**. Until then:

1. Download `wavu-fiji-<version>.zip` from the
   [latest release](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/releases/latest).
2. Unzip it **into your Fiji folder** (`Fiji.app`). This adds
   `scripts/Plugins/Wavu/`.
3. Restart Fiji. A **Plugins > Wavu** menu appears.
4. Run **Plugins > Wavu > Setup Python (pixi)** once. It downloads the
   official single-file `pixi` for your system from
   [prefix-dev/pixi releases](https://github.com/prefix-dev/pixi/releases),
   checks its sha256 against the release checksum file, and installs it into
   `Fiji.app/wavu/`. If that folder is read-only, it uses `~/.wavu/bin`
   instead. Skip this step if `pixi` is already on your PATH.

You need nothing else: no Python install, no conda, no compiler and no Java
build.

## Quick start

1. Get a script folder. You can download the
   [template](templates/wavu-script), or, with a clone of this repo, run
   `pixi run new-script my_analysis`.
2. In Fiji, open an image, then choose **Plugins > Wavu > Run Python Script**
   and pick the folder.
3. The first run builds that folder's environment. This takes a few minutes,
   once. After that, fill in the dialog and press OK. The blurred image opens.
   Press **Esc** to cancel a run.

A script is a plain Python file:

```python
PARAMS = {
    "image": {"type": "image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
}

def run(ctx, inputs, params):
    from scipy import ndimage
    ctx.log("blurring...")
    return {"blurred": ndimage.gaussian_filter(inputs["image"], params["sigma"])}
```

The full contract is in [docs/script-contract.md](docs/script-contract.md).
You can test a script without Fiji using `wavu.testing.FakeCtx`.

## Launch modes

| # | How the worker starts | When to use it |
|---|---|---|
| 1 | **Automatic.** Fiji runs `pixi run --manifest-path <folder>/pixi.toml wavu-worker --script-dir <folder>`. Wavu downloads pixi if needed. | The default. |
| 2 | **By hand.** In the script folder, run `pixi run worker` (or `pixi run debug` for VS Code), then use **Plugins > Wavu > Connect to Running Worker**. The worker writes its port and token to `~/.wavu/worker.json`. | Developing a script, or keeping one worker alive across Fiji restarts. |
| 3 | **Container.** `docker run --rm -p 127.0.0.1:8765:8765 -e WAVU_TOKEN=pick-one -v /my/data:/data ghcr.io/oxford-zeiss-centre-of-excellence/wavu-worker`, then **Connect to Running Worker** with handshake file `/my/data/.wavu/worker.json`, host folder `/my/data` and container folder `/data`. | Locked-down machines, or reproducing an exact environment. The image is built from the committed `pixi.lock`. See the [Dockerfile](Dockerfile) for building other script folders. |

Each release also includes **offline bundles** (`wavu-offline-*.zip`, made
with pixi-pack). They hold the template environment and the wavu wheel, for
machines with no internet. See `packaging/bundle/README-offline.txt`.

## Debugging in VS Code

Every script folder has `.vscode/launch.json` with **Attach to Wavu worker**.
To use it, either tick *Debug in VS Code* in the Run dialog, or run
`pixi run debug` and connect. Then attach from VS Code and run the script from
Fiji. VS Code stops at your breakpoints.

## Examples

- [`templates/wavu-script`](templates/wavu-script): Gaussian blur. This is the
  boilerplate for new scripts.
- [`examples/cellpose_nuclei`](examples/cellpose_nuclei): Cellpose nuclei
  segmentation, returning a label image and an ImageJ RoiSet. It has a CPU/MPS
  environment and an optional CUDA environment.

Using napari instead of Fiji? See the companion
[Napari-Pixi](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Napari-Pixi)
workspace. Its environment layout, including the `dl` PyTorch CUDA/MPS
environment, is the model for the examples here.

## Limitations

- Data must be small: see the scope section above. The client sends only one
  image per `image` parameter, plus plain values.
- Cancelling is cooperative. A script must check `ctx.cancelled()`, because a
  running Python call cannot be interrupted safely from outside.
- The first run of a script folder downloads its environment. For heavy
  frameworks like PyTorch that can be 1-2 GB.
- Fiji integration is through ImageJ 1.x `ImagePlus`, one image per input.
  Label images come back as 16-bit, or 32-bit float when there are more than
  65535 labels.
- Wavu is new. Expect rough edges and
  [report them](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/issues).

## More

- [docs/script-contract.md](docs/script-contract.md): what a script must look
  like.
- [docs/protocol.md](docs/protocol.md): the HTTP API between Fiji and the
  worker.
- [docs/decisions.md](docs/decisions.md): why it is built this way.
- [docs/development.md](docs/development.md): tests, the Fiji smoke test and
  releases.
- [docs/test-data.md](docs/test-data.md): the test image, its licence and
  attribution.
- [CONTRIBUTING.md](CONTRIBUTING.md)

## Licence and citation

GPL-3.0-or-later. See [LICENSE](LICENSE). If Wavu helps your research, please
cite it using [CITATION.cff](CITATION.cff). Releases are archived on Zenodo.
