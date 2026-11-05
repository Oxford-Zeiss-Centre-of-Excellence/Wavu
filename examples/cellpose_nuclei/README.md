# Cellpose nuclei (Wavu example)

Segments nuclei in a single-channel 2-D image (DAPI, Hoechst, H2B-GFP...) with
[Cellpose](https://github.com/MouseLand/cellpose)'s `nuclei` model (Cellpose 3)
and returns:

- `labels` -- a 16-bit label image (Fiji shows it with the glasbey LUT),
- `rois` -- every nucleus outline as an ImageJ RoiSet (opened in the ROI Manager),
- `count` -- the number of nuclei (printed to the Log).

## Use from Fiji

1. Open a 2-D nuclei image (one channel, one plane).
2. **Plugins > Wavu > Run Python Script...**, choose this folder.
3. The first start installs PyTorch + Cellpose (1-2 GB, several minutes, once).
   Leave *diameter* at 0 to let Cellpose estimate it.

## GPU

- Apple silicon: MPS works in the default environment.
- NVIDIA (Windows/Linux): use the `cuda` environment -- see the comment at the
  top of `pixi.toml` (same pattern as the org's Napari-Pixi `dl` environment).

## Status

**Not run locally while writing this first version** -- it is exercised only by
the weekly CI job (`.github/workflows/weekly.yml`). The test (`pixi run test`
in this folder) segments a synthetic image and, when the Cell Tracking Challenge
frame has been fetched (`pixi run fetch-test-data` at the repo root), checks the
result against that frame's ground-truth segmentation.

Cite Cellpose if you use it: Stringer et al., *Nature Methods* 18, 100-106 (2021).
