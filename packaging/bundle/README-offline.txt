Wavu offline bundle (no internet needed after download)
======================================================

Contents:
  environment.sh / environment.ps1   self-extracting environment (pixi-pack)
  wavu-<version>-py3-none-any.whl    the Wavu worker
  wavu-script/                       the example (Gaussian blur) script folder

1. Unpack the environment:
     Linux/macOS:  sh environment.sh            -> creates ./env and activate.sh
     Windows:      powershell -ExecutionPolicy Bypass -File environment.ps1
2. Install Wavu into it (offline):
     Linux/macOS:  ./env/bin/python -m pip install --no-deps --no-index wavu-*.whl
     Windows:      .\env\python.exe -m pip install --no-deps --no-index (Get-Item wavu-*.whl)
3. Start the worker (launch mode 2):
     ./env/bin/wavu-worker --script-dir wavu-script --handshake-file --detached
     (Windows: .\env\Scripts\wavu-worker.exe ...)
4. Fiji: Plugins > Wavu > Connect to Running Worker  (handshake file ~/.wavu/worker.json)

This bundle carries one fixed environment (numpy, scipy, tifffile). Scripts
that need other packages need their own environment -- use pixi online, or
build your own bundle with `pixi exec pixi-pack` from the script's pixi.toml.
