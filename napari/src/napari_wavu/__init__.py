"""wavu-napari: the napari frontend of Wavu (in the Wavu repository, napari/).

Runs Wavu scripts from napari, each in its own pixi environment.

The dock widget (Plugins › Wavu) starts a ``wavu-worker`` for a script folder
through ``wavu.client``, builds a form from the script's PARAMS, sends the
chosen layers and adds the results back as layers.
"""

from napari_wavu._widget import WavuWidget

__all__ = ["WavuWidget"]
