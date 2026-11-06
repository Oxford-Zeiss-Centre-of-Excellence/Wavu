# wavu-napari

The [napari](https://napari.org) frontend of Wavu. It adds
**Plugins › Run Python Script (Wavu)**: pick a Wavu script folder, fill in the
form built from its `PARAMS`, and the script runs in its own
[pixi](https://pixi.sh) environment through a `wavu-worker`. Results come back
as Image, Labels or Shapes layers and tables. The same script folders work in
Fiji (`fiji/`) and napari.

To use a worker started elsewhere (a container, another machine), tick
**Remote / container**, fill in the handshake file, host and the shared
folder's two names, and press **Connect to running worker**
([guide](https://oxford-zeiss-centre-of-excellence.github.io/Wavu/write/container/)).

## Start

From a clone of the Wavu repository:

```bash
pixi run -e napari napari
```

The first start installs napari (a few minutes, once).

Step-by-step guide:
<https://oxford-zeiss-centre-of-excellence.github.io/Wavu/napari/install/>

## Tests

```bash
pixi run -e napari test-napari              # conversion + widget tests (Qt offscreen)
pixi run -e napari test-napari-integration  # a real worker in templates/wavu-script, through pixi
```

GPL-3.0-or-later, like Wavu.
