"""Layer <-> Wavu conversions (no Qt, no worker)."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from napari_wavu._convert import image_layer, layer_input, output_layers, table_rows
from wavu.client import Output


def layer(data, **kw):
    return SimpleNamespace(data=data, name=kw.pop("name", "cells"), scale=kw.pop("scale", (1.0, 1.0)),
                           units=kw.pop("units", ("pixel", "pixel")), rgb=kw.pop("rgb", False), **kw)


def test_layer_input_sends_the_array_and_pixel_size():
    arr, meta = layer_input(layer(np.ones((4, 5), np.uint16), scale=(0.5, 0.5), units=("micrometer", "micrometer")))
    assert arr.shape == (4, 5) and meta == {"title": "cells", "pixel_um": 0.5}


def test_layer_input_ignores_unit_scale_and_takes_the_finest_multiscale_level():
    pyramid = [np.zeros((8, 8)), np.zeros((4, 4))]
    arr, meta = layer_input(layer(pyramid, multiscale=True))
    assert arr.shape == (8, 8) and "pixel_um" not in meta


def test_integer_outputs_named_like_labels_become_labels():
    data, kw, kind = image_layer("labels", np.zeros((3, 3), np.uint16), {"pixel_um": 0.25})
    assert kind == "labels" and kw["scale"] == (0.25, 0.25)
    assert image_layer("blurred", np.zeros((3, 3), np.uint16), {})[2] == "image"
    assert image_layer("blurred", np.zeros((3, 3), np.uint16), {"napari": "labels"})[2] == "labels"
    assert image_layer("mask_prob", np.zeros((3, 3), np.float32), {})[2] == "image"


def test_channel_axis_and_names_come_from_meta():
    _, kw, kind = image_layer("img", np.zeros((2, 5, 6), np.float32),
                              {"axes": "CYX", "channel_names": ["DAPI", "GFP"], "pixel_um": 1.5})
    assert kind == "image" and kw["channel_axis"] == 0
    assert kw["name"] == ["img [DAPI]", "img [GFP]"] and kw["scale"] == (1.5, 1.5)


def test_output_layers_maps_every_kind(tmp_path):
    import roifile

    roi = roifile.ImagejRoi.frompoints([[3, 2], [9, 2], [9, 6], [3, 6]])
    zip_path = tmp_path / "RoiSet.zip"
    roifile.roiwrite(zip_path, [roi])
    from wavu import RoiSet

    outs = {
        "labels": Output("labels", "image", np.zeros((4, 4), np.uint16)),
        "rois": Output("rois", "rois", RoiSet(zip_path)),
        "rows": Output("rows", "table", [{"a": 1}]),
        "count": Output("count", "value", 3),
    }
    layers, notes = output_layers(outs)
    kinds = [k for _, _, k in layers]
    assert kinds == ["labels", "shapes"]
    poly = layers[1][0][0]
    assert poly[0].tolist() == [2.0, 3.0]  # (row, col) = (y, x)
    assert "count = 3" in notes and any("rows" in n for n in notes)


def test_table_rows_from_dicts_and_dataframes():
    import pandas as pd

    assert table_rows([{"a": 1}, {"b": 2}]) == (["a", "b"], [[1, ""], ["", 2]])
    cols, rows = table_rows(pd.DataFrame({"x": [1, 2]}))
    assert cols == ["x"] and rows == [[1], [2]]
