"""Script discovery and the PARAMS schema (docs/script-contract.md)."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

PARAM_TYPES = ("float", "int", "str", "bool", "choice", "image")


class ScriptError(ValueError):
    """A script or a request for it does not follow the contract."""


@dataclass
class ScriptInfo:
    name: str
    path: Path
    module: ModuleType
    params: dict[str, dict[str, Any]]
    doc: str

    def schema(self) -> dict[str, Any]:
        return {"name": self.name, "doc": self.doc, "params": self.params}


def is_script_file(path: Path) -> bool:
    n = path.name
    return (
        path.suffix == ".py"
        and not n.startswith(("_", "test_", "."))
        and not n.endswith("_test.py")
        and n not in {"conftest.py", "setup.py", "noxfile.py"}
    )


def load_module(path: Path) -> ModuleType:
    """Import a script file by path. Its folder goes on sys.path for helpers."""
    path = Path(path).resolve()
    folder = str(path.parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    spec = importlib.util.spec_from_file_location(f"wavu_script_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ScriptError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def normalize_params(raw: Any, where: str = "PARAMS") -> dict[str, dict[str, Any]]:
    """Validate a PARAMS dict and fill in labels; raise ScriptError if wrong."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ScriptError(f"{where} must be a dict, got {type(raw).__name__}")
    out: dict[str, dict[str, Any]] = {}
    for name, spec in raw.items():
        if not isinstance(name, str) or not name.isidentifier():
            raise ScriptError(f"{where}: parameter name {name!r} is not a valid identifier")
        if not isinstance(spec, dict):
            raise ScriptError(f"{where}[{name!r}] must be a dict")
        ptype = spec.get("type")
        if ptype not in PARAM_TYPES:
            raise ScriptError(f"{where}[{name!r}]: type must be one of {PARAM_TYPES}, got {ptype!r}")
        s = dict(spec)
        s.setdefault("label", name.replace("_", " ").capitalize())
        if ptype == "choice":
            choices = s.get("choices")
            if not isinstance(choices, (list, tuple)) or not choices:
                raise ScriptError(f"{where}[{name!r}]: a choice needs a non-empty 'choices' list")
            s["choices"] = [str(c) for c in choices]
            s.setdefault("default", s["choices"][0])
            if str(s["default"]) not in s["choices"]:
                raise ScriptError(f"{where}[{name!r}]: default {s['default']!r} not in choices")
        elif ptype != "image":
            if "default" not in s:
                raise ScriptError(f"{where}[{name!r}]: a default value is required")
            s["default"] = _coerce(name, ptype, s["default"])
        out[name] = s
    return out


def _coerce(name: str, ptype: str, value: Any) -> Any:
    try:
        if ptype == "float":
            return float(value)
        if ptype == "int":
            if isinstance(value, float) and not value.is_integer():
                raise ValueError("not a whole number")
            return int(value)
        if ptype == "bool":
            if isinstance(value, str):
                if value.lower() in {"true", "1", "yes", "on"}:
                    return True
                if value.lower() in {"false", "0", "no", "off", ""}:
                    return False
                raise ValueError("not a boolean")
            return bool(value)
        return str(value)
    except (TypeError, ValueError) as e:
        raise ScriptError(f"parameter {name!r}: cannot use {value!r} as {ptype} ({e})") from None


def coerce_params(schema: dict[str, dict[str, Any]], given: dict[str, Any] | None) -> dict[str, Any]:
    """Defaults + type conversion for a run request. Image params are inputs, not params."""
    given = dict(given or {})
    out: dict[str, Any] = {}
    for name, spec in schema.items():
        if spec["type"] == "image":
            given.pop(name, None)
            continue
        value = given.pop(name, spec.get("default"))
        if spec["type"] == "choice":
            value = str(value)
            if value not in spec["choices"]:
                raise ScriptError(f"parameter {name!r}: {value!r} is not one of {spec['choices']}")
        else:
            value = _coerce(name, spec["type"], value)
        out[name] = value
    if given:
        raise ScriptError(f"unknown parameter(s): {', '.join(sorted(given))}")
    return out


def load_script(path: Path) -> ScriptInfo:
    path = Path(path)
    mod = load_module(path)
    run = getattr(mod, "run", None)
    if not callable(run):
        raise ScriptError(f"{path.name}: no run(ctx, inputs, params) function")
    if len(inspect.signature(run).parameters) != 3:
        raise ScriptError(f"{path.name}: run must take exactly (ctx, inputs, params)")
    params = normalize_params(getattr(mod, "PARAMS", {}), f"{path.name}: PARAMS")
    doc = inspect.cleandoc(mod.__doc__ or "")
    return ScriptInfo(name=path.stem, path=path, module=mod, params=params, doc=doc)


def discover(script_dir: Path) -> tuple[dict[str, ScriptInfo], dict[str, str]]:
    """All scripts in a folder (top level only), plus import errors by name."""
    scripts: dict[str, ScriptInfo] = {}
    errors: dict[str, str] = {}
    for path in sorted(Path(script_dir).glob("*.py")):
        if not is_script_file(path):
            continue
        try:
            mod_text = path.read_text(encoding="utf-8", errors="replace")
            if "def run" not in mod_text:
                continue  # a helper module, not a script
            scripts[path.stem] = load_script(path)
        except Exception as e:  # noqa: BLE001 - report, don't crash the worker
            errors[path.stem] = f"{type(e).__name__}: {e}"
    return scripts, errors
