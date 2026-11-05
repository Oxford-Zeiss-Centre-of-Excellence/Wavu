"""PARAMS validation, codec conversions, FakeCtx and the CLI -- no server involved."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import wavu
from wavu import cli
from wavu.codec import decode_array, decode_input, encode_array, encode_output, imagej_array
from wavu.scripts import ScriptError, coerce_params, discover, normalize_params
from wavu.testing import FakeCtx, run_script

from conftest import REPO, SCRIPTS


# -- PARAMS -------------------------------------------------------------------


@pytest.mark.parametrize(
    "params,fragment",
    [
        ([1, 2], "must be a dict"),
        ({"x": {"type": "complex", "default": 1}}, "type must be one of"),
        ({"x": {"type": "float"}}, "default value is required"),
        ({"x": {"type": "choice", "choices": []}}, "non-empty"),
        ({"x": {"type": "choice", "choices": ["a"], "default": "b"}}, "not in choices"),
        ({"not valid": {"type": "int", "default": 1}}, "identifier"),
        ({"x": {"type": "int", "default": 1.5}}, "whole number"),
    ],
)
def test_bad_params_are_rejected(params, fragment):
    with pytest.raises(ScriptError, match=fragment):
        normalize_params(params)


def test_coerce_fills_defaults_and_converts_strings():
    schema = normalize_params(
        {
            "img": {"type": "image"},
            "n": {"type": "int", "default": 2},
            "on": {"type": "bool", "default": True},
            "mode": {"type": "choice", "choices": ["x", "y"]},
        }
    )
    assert schema["mode"]["default"] == "x"
    assert coerce_params(schema, {"n": "5", "on": "false", "img": "ignored"}) == {"n": 5, "on": False, "mode": "x"}


def test_discover_skips_tests_helpers_and_private_files():
    scripts, errors = discover(SCRIPTS)
    assert "helper_mod" not in scripts and "conftest" not in scripts
    assert set(errors) == {"broken"}


# -- codec --------------------------------------------------------------------


@pytest.mark.parametrize(
    "dtype,expected",
    [(bool, "uint8"), (np.int8, "uint16"), (np.int32, "uint16"), (np.uint32, "uint16"), (np.float64, "float32"),
     (np.uint8, "uint8"), (np.uint16, "uint16"), (np.float32, "float32")],
)
def test_imagej_dtypes(dtype, expected):
    assert imagej_array(np.ones((2, 2), dtype=dtype)).dtype.name == expected


def test_negative_or_huge_integers_become_float32():
    assert imagej_array(np.array([[-1, 2]], dtype=np.int32)).dtype == np.float32
    assert imagej_array(np.array([[70000]], dtype=np.int64)).dtype == np.float32


def test_encode_decode_round_trip_big_endian_input():
    a = np.arange(6, dtype=">u2").reshape(2, 3)
    np.testing.assert_array_equal(decode_array(json.loads(json.dumps(encode_array(a)))), a)


def test_decode_input_by_kind(tmp_path):
    (tmp_path / "t.csv").write_text("a,b\n1,2\n")
    table, _ = decode_input({"path": str(tmp_path / "t.csv")})
    assert list(table.columns) == ["a", "b"]
    (tmp_path / "RoiSet.zip").write_bytes(b"PK")
    rs, _ = decode_input({"path": str(tmp_path / "RoiSet.zip")})
    assert isinstance(rs, wavu.RoiSet)
    (tmp_path / "x.zarr").mkdir()
    p, meta = decode_input({"path": str(tmp_path / "x.zarr"), "meta": {"pixel_um": 1}})
    assert p == tmp_path / "x.zarr" and meta == {"pixel_um": 1}


def test_unsupported_output_type_is_a_clear_error(tmp_path):
    with pytest.raises(TypeError, match="don't know how to return a set"):
        encode_output("x", {1, 2}, tmp_path)
    with pytest.raises(TypeError, match="at least 2 dimensions"):
        encode_output("x", np.ones(3), tmp_path)


# -- FakeCtx / run_script -----------------------------------------------------


def test_fakectx_records_and_cancels():
    ctx = FakeCtx(cancel_after=1)
    ctx.log("a")
    ctx.progress(2)
    assert ctx.messages == ["a"] and ctx.progress_values == [1.0]
    assert ctx.cancelled() is False and ctx.cancelled() is True
    with pytest.raises(wavu.Cancelled):
        ctx.check_cancelled()
    assert ctx.tmpdir.is_dir()


def test_run_script_applies_defaults_like_the_worker():
    out = run_script(SCRIPTS / "echo.py", {"image": np.ones((2, 2))}, {"factor": "2"})
    assert out["image"].sum() == 8 and out["params"] == "hi|False|b|0.5"


# -- CLI ----------------------------------------------------------------------


def test_cli_run_writes_outputs(tmp_path, capsys):
    import tifffile

    tifffile.imwrite(tmp_path / "in.tif", np.full((4, 4), 7, np.uint8))
    assert cli.main(["run", str(SCRIPTS / "echo.py"), "--in", f"image={tmp_path / 'in.tif'}",
                     "--param", "factor=2", "--out", str(tmp_path / "out")]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert tifffile.imread(summary["image"]["path"]).max() == 14


def test_new_script_copies_template_and_points_at_this_checkout(tmp_path):
    assert cli.main(["new-script", "my_analysis", "--dest", str(tmp_path)]) == 0
    dest = tmp_path / "my_analysis"
    assert {p.name for p in dest.iterdir()} >= {"script.py", "test_script.py", "pixi.toml", "README.md", ".vscode"}
    assert not (dest / ".pixi").exists() and not (dest / "pixi.lock").exists()
    toml = (dest / "pixi.toml").read_text()
    assert 'name = "my_analysis"' in toml
    line = next(l for l in toml.splitlines() if l.startswith("wavu ="))
    assert "editable = true" in line
    rel = line.split('path = "')[1].split('"')[0]
    assert ((dest / rel) / "pyproject.toml").resolve() == (REPO / "pyproject.toml").resolve()


@pytest.mark.parametrize("source,fragment", [("release", "releases/download/v"), ("pypi", 'wavu = ">=0.1"')])
def test_new_script_wavu_sources(tmp_path, source, fragment):
    cli.main(["new-script", "s", "--dest", str(tmp_path), "--wavu-source", source])
    assert fragment in (tmp_path / "s" / "pixi.toml").read_text()


def test_new_script_refuses_bad_names_and_existing_folders(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["new-script", "../evil", "--dest", str(tmp_path)])
    (tmp_path / "taken").mkdir()
    with pytest.raises(SystemExit):
        cli.main(["new-script", "taken", "--dest", str(tmp_path)])


def test_template_path_dependency_resolves_to_the_repo():
    toml = (REPO / "templates" / "wavu-script" / "pixi.toml").read_text()
    line = next(l for l in toml.splitlines() if l.startswith("wavu ="))
    assert 'path = "../.."' in line
    assert (REPO / "templates" / "wavu-script" / "../.." / "pyproject.toml").resolve() == (REPO / "pyproject.toml").resolve()


def test_fiji_zip_fills_in_the_version(tmp_path):
    import importlib.util
    import zipfile

    spec = importlib.util.spec_from_file_location("make_fiji_zip", REPO / "tools" / "make_fiji_zip.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main(["1.2.3", "--out", str(tmp_path)]) == 0
    with zipfile.ZipFile(tmp_path / "wavu-fiji-1.2.3.zip") as z:
        names = z.namelist()
        lib = z.read("scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt").decode()
    assert "scripts/Plugins/Wavu/Run_Python_Script.groovy" in names
    assert 'VERSION = "1.2.3"' in lib and "@WAVU_VERSION@" not in lib
