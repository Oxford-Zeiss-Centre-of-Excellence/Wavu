"""Wavu (Fijian for "bridge"): run Python scripts from Fiji, each in its own pixi env.

A script is a plain module with ``PARAMS`` and ``run(ctx, inputs, params)``;
see docs/script-contract.md. ``wavu-worker`` serves one script folder over a
small authenticated HTTP/JSON API that the Fiji client scripts talk to.
"""

from wavu.types import Cancelled, Image, Roi, RoiSet

try:  # written by hatch-vcs at build/install time from the git tag
    from wavu._version import __version__
except ImportError:  # pragma: no cover - running from a bare source tree
    __version__ = "0.0.0"

__all__ = ["Cancelled", "Image", "Roi", "RoiSet", "__version__"]
