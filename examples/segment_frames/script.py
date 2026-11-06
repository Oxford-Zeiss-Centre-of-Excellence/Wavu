"""Segment frames -- Gaussian smooth, threshold and label every frame of a time-lapse.

Works on a time-lapse (T, Y, X) or a single 2-D image. Labels restart at 1 in
every frame. Returns the label stack, one row per detected object (frame,
label, y, x, area, mean_intensity) and the number of objects per frame --
the detections table is what a tracking step (examples/track_trackpy) takes.
"""

import numpy as np

import wavu

PARAMS = {
    "image": {"type": "image", "label": "Time-lapse (T, Y, X) or 2-D image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Smoothing sigma (pixels)"},
    "threshold": {"type": "choice", "choices": ["otsu", "li", "triangle"], "default": "otsu",
                  "label": "Threshold method"},
    "min_area": {"type": "int", "default": 30, "label": "Minimum object area (pixels)"},
}


def run(ctx, inputs, params):
    import pandas as pd
    from skimage import filters, measure

    image = np.asarray(inputs["image"])
    if image.ndim == 2:
        image = image[np.newaxis]
    if image.ndim != 3:
        raise ValueError(f"expected a time-lapse (T, Y, X) or a 2-D image, got shape {image.shape} "
                         "-- pick one channel / Z plane in Fiji first")
    method = {"otsu": filters.threshold_otsu, "li": filters.threshold_li,
              "triangle": filters.threshold_triangle}[params["threshold"]]
    n_frames = image.shape[0]
    ctx.log(f"Segmenting {n_frames} frame(s) of {image.shape[1:]} ({params['threshold']}, sigma={params['sigma']})")

    labels = np.zeros(image.shape, dtype=np.uint16)
    rows, counts = [], []
    for t in range(n_frames):
        if ctx.cancelled():
            ctx.log(f"Cancelled after {t} frame(s)")
            return {}
        frame = image[t].astype(np.float32)
        smooth = filters.gaussian(frame, sigma=params["sigma"], preserve_range=True) if params["sigma"] > 0 else frame
        mask = smooth > method(smooth)
        lab = measure.label(mask)
        sizes = np.bincount(lab.ravel())
        keep = sizes >= params["min_area"]
        keep[0] = False
        lab = measure.label(keep[lab])  # small objects removed, labels 1..n again
        labels[t] = lab
        for p in measure.regionprops(lab, intensity_image=frame):
            y, x = p.centroid
            rows.append({"frame": t, "label": int(p.label), "y": float(y), "x": float(x),
                         "area": int(p.area), "mean_intensity": float(p.intensity_mean)})
        counts.append({"frame": t, "count": int(lab.max())})
        ctx.progress((t + 1) / n_frames)

    detections = pd.DataFrame(rows, columns=["frame", "label", "y", "x", "area", "mean_intensity"])
    count_per_frame = pd.DataFrame(counts, columns=["frame", "count"])
    ctx.log(f"{len(detections)} objects in total; per frame {count_per_frame['count'].min()}"
            f"-{count_per_frame['count'].max()}")
    pixel_um = (ctx.meta.get("image") or {}).get("pixel_um")
    return {
        "labels": wavu.Image(labels, pixel_um=pixel_um, axes="TYX"),
        "detections": detections,
        "count_per_frame": count_per_frame,
    }
