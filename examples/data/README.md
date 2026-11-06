# Example data

`demo_timelapse.tif` -- a **synthetic** nuclei time-lapse made by this repository
(`pixi run demo-data`, i.e. `tools/make_demo_timelapse.py`; numpy + tifffile,
fixed seed). No real data. CC0 / public domain.

- 30 frames, 256 x 256, 16-bit, ImageJ hyperstack (axes TYX),
  0.65 um/pixel, 5 min/frame.
- About 25 round nuclei on a dim noisy background, drifting with small random
  walks. Four divide (frames 6, 12, 17, 23), one leaves the field of view on
  the right (gone by frame 9), one enters from the left (visible from frame 19).
- True nuclei per frame (centre inside the image), frames 0-29:
  `25 25 25 25 25 25 26 26 26 25 25 25 26 26 26 26 26 27 27 28 28 28 28 29 29 29 29 29 29 29`
  (also stored in the TIFF's ImageJ *Info* property).

Used by `examples/segment_frames` and `examples/track_trackpy`.
