# My Wavu script

A Python script that Fiji runs through [Wavu](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu),
in its own [pixi](https://pixi.sh) environment.

| File | What it is |
|---|---|
| `script.py` | The script: `PARAMS` (the dialog) and `run(ctx, inputs, params)` |
| `test_script.py` | Tests that run without Fiji (`pixi run test`) |
| `pixi.toml` | This script's own environment -- add packages here |
| `.vscode/launch.json` | "Attach to Wavu worker" for breakpoints in VS Code |
| `.github/workflows/release.yml` | Tag `v*` → test, package for Fiji, GitHub Release |

## Run it from Fiji

1. Fiji: open an image.
2. **Plugins > Wavu > Run Python Script...**, choose this folder.
3. The first run builds the environment (a few minutes, once). Fill in the dialog, press OK.
   Logs appear in the Log window, progress in Fiji's status bar; press **Esc** to cancel.

## Run it from the command line

```
pixi run wavu run script.py --in image=cells.tif --param sigma=3 --out results
```

## Debug it in VS Code

1. Open this folder in VS Code (with the Python extension).
2. Either tick **Debug in VS Code** in Fiji's Run dialog, or start the worker
   yourself with `pixi run debug` and use **Plugins > Wavu > Connect to Running Worker**.
3. VS Code: **Run and Debug > Attach to Wavu worker**. Set breakpoints in `script.py`.
4. Run the script from Fiji; VS Code stops at your breakpoints.

## Release it

1. Run `pixi install` once and commit `pixi.lock` together with the rest of
   this folder, as its own git repository.
2. Push a tag: `git tag v1.0.0 && git push --tags`.
   `.github/workflows/release.yml` tests the script, runs `wavu package` and
   attaches `<name>-fiji.zip` to a GitHub Release. Users unzip it into
   `Fiji.app`. The menu location is `MENU` at the top of that workflow.
3. Optional: set the repository variables `PYPI_PUBLISH=true` or
   `FIJI_UPDATE_SITE=true` (see the comments in the workflow).

## Add a package

```
pixi add scikit-image        # from conda-forge
pixi add --pypi some-package # from PyPI
```

## The contract in one screen

- `PARAMS = {name: {"type": "float|int|str|bool|choice|image", "default": ..., "label": ..., "choices": [...]}}`
- `run(ctx, inputs, params)` gets numpy arrays in `inputs` (one per `image` parameter)
  and plain values in `params`; it returns a dict whose values are numpy arrays
  (opened as images), DataFrames or lists of dicts (opened as tables),
  `wavu.RoiSet(path)` (opened in the ROI Manager) or plain values (printed to the Log).
- `ctx.log(msg)`, `ctx.progress(0..1)`, `ctx.cancelled()`, `ctx.tmpdir`, `ctx.meta[name]`
  (pixel size, channel names of each input image).

Keep data small (one image that fits comfortably in memory). For big data use
OME-Zarr and a chunked batch/HPC workflow instead.
