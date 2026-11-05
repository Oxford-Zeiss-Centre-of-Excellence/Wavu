# Test data

`pixi run fetch-test-data` writes these files to
`tests/data/Fluo-N2DH-GOWT1/`, which git ignores:

| file | what | sha256 of the original zip member |
|---|---|---|
| `t021.tif` | Fluo-N2DH-GOWT1, training sequence 01, frame 21. 1024×1024 uint8, GFP-labelled nuclei of GOWT1 mouse embryonic stem cells | `e238390fc4d1edf5e38e24638b4a9165a10b8e94252b14c8c85fe2c6f32d35e5` |
| `man_seg021.tif` | The gold-standard segmentation of that frame, with 24 nuclei (uint16 labels) | `abd1dee1d6ace107c908819100221774c57e13c150456e92e6d08bc59a83d94a` |

The script downloads the whole training archive once,
`https://data.celltrackingchallenge.net/training-datasets/Fluo-N2DH-GOWT1.zip`
(59,331,035 bytes ≈ 57 MiB; the CTC site says "53 MB"), and caches it in
`~/.cache/wavu/`. Set `WAVU_CACHE` to use another folder. It then checks both
members against the hashes above and re-saves them uncompressed. The
originals are LZW-compressed and would need `imagecodecs` to read.

**Why this dataset.** It is the smallest CTC 2-D *nuclei* training set. The
alternatives were Fluo-N2DL-HeLa (182 MB) and Fluo-N2DH-SIM+ (91 MB,
simulated). Frame 21 is used because most GOWT1 `SEG` frames annotate only
1-3 nuclei, while frame 21 annotates all 24. No crop is needed: 1 MB.

## Licence and terms (checked 2026-11-05)

The CTC website states no open licence for the data. Its
[dataset terms](https://celltrackingchallenge.net/datasets/) say, in summary:

1. Publications using the data must cite Maška et al., *Nature Methods* 20,
   1010-1020 (2023), https://doi.org/10.1038/s41592-023-01879-y, and
   acknowledge the Cell Tracking Challenge.
2. CTC-related use needs no explicit consent.
3. **Public scientific use outside the CTC requires explicit permission from
   the challenge organizers.**
4. Commercial use requires permission from the organizers and the data
   providers.
5. **Cloning the datasets or their parts, including reference annotations, is
   prohibited.** Link to the download pages instead.

Wavu therefore never commits or redistributes the files. It downloads them
from the official server on demand, for local and CI tests only.

> **Owner action:** term 3 arguably covers using the frame in a *public*
> project's CI. Either ask the CTC organizers for permission
> (https://celltrackingchallenge.net/contact-us/), or, if declined, switch
> `tools/fetch_test_data.py` to an openly licensed nuclei image. For example,
> the BBBC039 / BBBC038 (Data Science Bowl 2018) images are CC0/CC-BY. Right
> now only the weekly CI job (`weekly.yml` → cellpose) fetches it. The
> default CI does not.

## Attribution

> Fluo-N2DH-GOWT1 from the Cell Tracking Challenge
> (https://celltrackingchallenge.net). M. Maška et al., "The Cell Tracking
> Challenge: 10 years of objective benchmarking", *Nature Methods* 20,
> 1010-1020 (2023).

`SOURCE.txt`, written next to the files, repeats this.
