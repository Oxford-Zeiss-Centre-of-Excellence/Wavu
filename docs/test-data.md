# Test data

These files are **committed** under `tests/data/BBBC039/`. They are 0.74 MB
together and CC0, so every CI run and every clone has them:

| file | what | sha256 (identical to the published zip member) |
|---|---|---|
| `A02_s1.tif` | BBBC039 `images/IXMtest_A02_s1_w1051DAA7C-7042-435F-99F0-1E847D9B42CB.tif`: U2OS nuclei, Hoechst, 520×696 uint16 | `9eacee0e5a4c29af70307af4d310320632e31ed84b4d8b5fd4fce42930f780ec` |
| `A02_s1_mask.png` | the matching `masks/...png`, the ground truth with 110 nuclei | `c56c246edcd456f81fb0d61d318c2b7a378afba207bd0b409834db16d30cfb72` |
| `SOURCE.txt` | licence and citation | |

The files are unmodified. In the mask PNG, channel 0 holds a 4-colouring
(0 = background, 1-3 = colours). Each nucleus is one connected component of
one colour. `bbbc039_labels()` in `tests/test_bbbc039.py` and in
`examples/cellpose_nuclei/test_script.py` turns that into a label image.

`pixi run fetch-test-data` checks both sha256 sums. If the files are
missing, it downloads `images.zip` (77,915,748 bytes) and `masks.zip`
(2,753,811 bytes) from https://data.broadinstitute.org/bbbc/BBBC039/ into
`~/.cache/wavu/BBBC039/` (or `$WAVU_CACHE`) and extracts only this pair. The
BBBC page offers no per-file URLs, only these zips.

**Why this dataset.** It is real 2-D fluorescent nuclei with expert
instance masks (200 fields in total), the licence is CC0, and one field is
small enough to commit.

## Licence (checked 2026-11-05 on https://bbbc.broadinstitute.org/BBBC039)

> Copyright: CC0. To the extent possible under law, the various contributors
> of the imagesets have waived all copyright and related or neighboring
> rights to BBBC039v1.

## Citation (as requested on that page)

> We used image set BBBC039v1 Caicedo et al. 2018, available from the Broad
> Bioimage Benchmark Collection [Ljosa et al., Nature Methods, 2012].

- V. Ljosa, K. L. Sokolnicki, A. E. Carpenter, "Annotated high-throughput
  microscopy image sets for validation", *Nature Methods* 9, 637 (2012),
  https://doi.org/10.1038/nmeth.2083
- J. C. Caicedo et al., "Evaluation of Deep Learning Strategies for Nucleus
  Segmentation in Fluorescence Images", *Cytometry Part A* (2019),
  https://doi.org/10.1002/cyto.a.23863. This is the publication behind BBBC039;
  the BBBC page dates it 2018.
