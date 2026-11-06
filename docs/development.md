# Development

All you need is pixi. Everything else comes from `pixi.toml`.

| command | what it does |
|---|---|
| `pixi run test` | Unit and protocol tests. They start real `wavu-worker` subprocesses against `tests/scripts/` and run the template's own tests. |
| `pixi run test-integration` | Starts a worker through `pixi run` in `templates/wavu-script`'s own environment and runs the blur. |
| `WAVU_FIJI=<Fiji.app> pixi run test-fiji` | Headless Fiji smoke test. Fiji runs `tests/fiji/smoke_test.groovy`, which loads the real client library, starts a worker for the template through pixi, and blurs a synthetic 16-bit image. It does this once with inline transfer and once through TIFF files, and checks size, type, blur and calibration. Set `WAVU_FIJI_LAUNCHER` to choose the launcher. |
| `WAVU_SMOKE_DAG=1 WAVU_FIJI=<Fiji.app> pixi run test-fiji` | Also runs both versions of the [Pipeline in Fiji](../guide/workflows/pipeline-fiji.md) guide page, `tests/fiji/dag_counting.groovy` (Groovy + TrackMate, headless) and `tests/fiji/dag_counting.ijm` (macro, `-batch`), on `examples/data/demo_timelapse.tif`. Checks the cells per frame against the truth (at most one off per frame), the track count and the saved CSV/PNG. It copies this checkout's `fiji/scripts/Plugins/Wavu` into the Fiji first, because both scripts load Wavu from Fiji's own folder as a user would. Off by default: the first run installs the `segment_frames` and `track_trackpy` environments (minutes). Do not run it while another process uses those folders' workers: pixi cannot refresh an environment whose `wavu-worker.exe` is in use (Windows). |
| `pixi run fetch-test-data` | Verifies the committed BBBC039 image and mask by sha256, and re-downloads them if they are missing (see [test-data.md](test-data.md)). |
| `pixi run worker` | [Launch mode 2](running-and-debugging.md#2-by-hand) for the template. |
| `pixi run new-script NAME` | Copies the template to `./NAME`. |
| `pixi run fiji-zip [VERSION]` | Builds `dist/wavu-fiji-<version>.zip`. |
| `pixi run -e build build` | Builds the wheel and sdist. |
| `pixi run --manifest-path examples/cellpose_nuclei/pixi.toml test` | The heavy cellpose test (weekly CI). |

## Verified locally (Windows 11, first version)

- `pixi run test`: all tests pass.
- `pixi run test-integration`: passes.
- The Fiji smoke test passes against a Fiji with **Java 1.8.0_452
  (Zulu 8), ImageJ 1.54p, Groovy 4.0.23**, using the legacy launcher:
  `WAVU_FIJI=D:/Downloads/Fiji.app WAVU_FIJI_LAUNCHER=ImageJ-win64.exe pixi run test-fiji`
- The newer Jaunch launcher (`fiji-windows-x64.exe`) in that same old
  installation exited with code 1 and printed nothing, even for a hello-world
  script. This is probably because it is paired with Java 8 there. CI uses
  the latest Fiji, with Java 21 and Jaunch on Linux. The `fiji-smoke` job is
  `continue-on-error` until it has been seen green there.
- Not run locally: the Docker image (Docker Desktop was not running), the
  cellpose example, and the screenshot capture.
  `pixi exec pixi-pack ... packaging/bundle` was run for linux-64 and
  produced a 137 MiB self-extracting bundle.

## Releases

Releases are fully automated. See [CONTRIBUTING.md](../CONTRIBUTING.md) and
[decisions.md](decisions.md) D9.
