# Screenshot list for the Wavu guide

Every image below is already referenced by the guide. To add a real
screenshot, **save a PNG with exactly this filename into this folder**
(`guide/assets/shots/`), replacing the grey placeholder. No Markdown edits
are needed. This file is excluded from the website (`exclude_docs` in
`mkdocs.yml`).

General tips:

- Use a fresh Fiji with default look and feel, English UI, at 100 % display
  scaling; light theme for VS Code shots unless noted.
- PNG, about **1200 × 750** px (16:10) unless noted; crop to the relevant
  window(s) rather than the full desktop. Keep text readable at 100 %
  zoom (don't shrink more than ~70 %).
- Hide personal paths/usernames where possible (e.g. put scripts in
  `C:\Users\demo\Documents` or `~/Documents`).
- The placeholders were drawn by `pixi run -e docs python tools/make_shot_placeholders.py`,
  which reads the table below. It never overwrites a file that is not a
  placeholder, so you can rerun it safely.

| File | Title (drawn on placeholder) | Page | What to open / click | What must be visible | Crop / size |
|---|---|---|---|---|---|
| `01-unzip-into-fiji.png` | Wavu unzipped into Fiji.app | Start › Install | Unzip `wavu-fiji-<version>.zip` into `Fiji.app`, then open `Fiji.app/scripts/Plugins/Wavu/` in Explorer/Finder | Path bar showing `Fiji.app › scripts › Plugins › Wavu`; the four `.groovy` files and the `lib` folder | File-manager window only, ~1200 × 750 |
| `02-plugins-wavu-menu.png` | Plugins › Wavu menu | Start › Install | Restart Fiji, open **Plugins › Wavu** | The four items: Connect to Running Worker, Run Python Script, Setup Python (pixi), Stop Worker | Fiji main window + open menu, ~1000 × 625 |
| `03-setup-python-ready.png` | Setup Python (pixi): Ready | Start › Install | **Plugins › Wavu › Setup Python (pixi)** on a machine without pixi | The "Ready: pixi x.y.z" message box, and behind it the Log with `Downloading pixi…`, `Checksum OK`, `pixi installed:` | Message box + Log, ~1200 × 750 |
| `04-choose-folder.png` | Choosing the script folder | Start › First run | Open Blobs; **Plugins › Wavu › Run Python Script** (no installed scripts yet) | Folder chooser titled "Wavu: choose a script folder (contains pixi.toml)" with `Wavu-Script-Template-main` selected | Chooser dialog only |
| `05-first-start-log.png` | First start: downloading packages | Start › First run | Same run, a few seconds after choosing the folder (delete the folder's `.pixi` first to force a first start) | Log with "First start of '…': downloading its Python packages…" and pixi output; status bar "Wavu: starting worker… Ns (Esc to cancel)" | Log + Fiji main window status bar |
| `06-run-dialog.png` | The "Wavu: script" dialog | Start › First run | When the worker is ready | Dialog "Wavu: script": description line, Image = blobs.gif, Sigma (pixels) 2.000, Edges reflect, Keep the input's pixel type ✓, Debug in VS Code ☐ | Dialog only, ~800 × 500 is fine |
| `07-blur-result.png` | Blobs and blobs-blurred | Start › First run | Press OK with defaults | `blobs.gif` and `blobs-blurred` side by side; Log showing "Running script …", "Blurring a (254, 256) uint8 image with sigma=2.0", "script finished" | Two image windows + Log, ~1200 × 750 |
| `08-vscode-browser-prompt.png` | Browser: open Visual Studio Code? | Write › Get the template | Click "Open the template in VS Code" on the guide page | The browser's "Open Visual Studio Code?" prompt (Chrome or Edge), with the guide page behind it | Browser window, ~1200 × 750 |
| `09-vscode-template-open.png` | Template open in VS Code | Write › Get the template | After the clone finishes and the folder opens | VS Code Explorer listing `.github`, `.vscode`, `pixi.toml`, `README.md`, `script.py`, `test_script.py`; `script.py` open showing `PARAMS` | VS Code window, ~1200 × 750 |
| `10-params-dialog.png` | Dialog built from PARAMS | Write › PARAMS | Make a script with the "Field types demo" `PARAMS` from the page (`image`, `sigma`, `n`, `name`, `fast`, `method`), open Blobs, run it | Dialog "Wavu: <script name>" with "Field types demo -- one of each." and all six fields: Nuclei image, Sigma (pixels), N, Name, Fast ✓, Method (otsu) | Dialog only |
| `11-outputs.png` | Labels, table and ROIs | Write › What you can return | Run `examples/cellpose_nuclei` on `tests/data/BBBC039/A02_s1.tif` (or the page's example on Blobs plus an RoiSet) | A label image with glasbey colours, a Results table, the ROI Manager with outlines shown on the input image | Several windows, ~1200 × 750 |
| `12-log-progress.png` | Log messages and progress bar | Write › Logs, progress and cancel | Run the template on a large stack (e.g. **File › Open Samples › T1 Head**) with Sigma 4 | Log lines from `ctx.log`, and Fiji's main window with the progress bar part-filled and "Wavu: script NN%" in the status bar | Fiji main window + Log |
| `13-error-dialog.png` | Error window and traceback | Help › Troubleshooting | Add `import skimage` inside `run` of the template without adding it to `pixi.toml`, Stop Worker, run | Error box "script failed: ModuleNotFoundError: No module named 'skimage' … (full traceback in the Log window)" and the traceback in the Log | Error box + Log |
| `14-script-folder-picker.png` | Script folder list | Share › With your lab | After installing a packaged tool and running one script folder, choose **Run Python Script** | Dialog "Wavu: run a Python script" with the "Script folder" drop-down open: `running: …`, `installed: my-tool`, `<choose a script folder...>` | Dialog with open drop-down |
| `15-lab-menu.png` | Plugins › My Lab › My Tool | Share › With your lab | Unzip a `wavu package` zip made with `--menu "My Lab>My Tool"` into Fiji.app, restart | **Plugins › My Lab › My Tool** open in the menu (Wavu menu visible nearby) | Fiji main window + menu |
| `16-vscode-breakpoint.png` | VS Code paused at a breakpoint | Help › Debug in VS Code | Tick "Debug in VS Code" in the dialog, attach with "Attach to Wavu worker", breakpoint on the first line of `run` | VS Code paused on the breakpoint in `script.py`, Variables panel showing `image` (shape), the debug toolbar | VS Code window, ~1200 × 750 |
