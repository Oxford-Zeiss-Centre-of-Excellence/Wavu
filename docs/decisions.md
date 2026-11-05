# Decisions

These are the reasons Wavu is shaped the way it is, written for a future
maintainer. The owner's constraints behind them: installation must be very
easy, the OS dependencies minimal, and maintenance must take at most 1% of the
owner's time.

## D1: HTTP/JSON on localhost, not gRPC, JNI or a Java plugin

The Fiji client talks to the worker with plain HTTP and JSON through
`java.net.HttpURLConnection`, which has been in the JDK since Java 1.1.

- **gRPC was rejected.** It would mean protobuf and gRPC jars inside Fiji.
  Fiji ships one flat classpath, so those jars would conflict with the
  versions other plugins bundle (Guava and Netty are the usual casualties).
  Fixing that means shading a jar, which means a Java build to maintain. That
  is far beyond the maintenance budget. gRPC's advantages, streaming and
  typed stubs, do not matter at "one small image per call".
- **JNI, embedded CPython and a Rust core were rejected** because they all
  need compiled artefacts per OS and architecture, and break when Fiji's JVM
  or the user's Python changes. They also cannot give each script its own
  environment.
- **Server-sent events** carry logs and progress. They are just lines of
  text on an open response, so they need no WebSocket library on either side.

## D2: The worker uses the standard library server

`http.server.ThreadingHTTPServer`, `json` and `threading` are enough for one
local client and a handful of requests. A web framework (FastAPI, Flask)
would add dependency churn to *every* script environment, because the worker
runs inside each script's env. It would also make the worker's dependencies
conflict with what scripts pin. numpy and tifffile are the only runtime
dependencies.

## D3: One pixi environment per script folder, and the worker runs inside it

`pixi run --manifest-path <folder>/pixi.toml wavu-worker ...` puts the worker
in the script's own environment, so `run()` is a plain function call: no
pickling, no subprocess per job. pixi is a single static binary that Wavu can
download and checksum on its own (D7). It handles conda and PyPI packages and
CUDA variants, and writes lock files for reproducibility and for the
container image. This is **dependency isolation, not a security sandbox**.

## D4: Small data only

Images go inline as base64 when ≤ 4 MiB and at most 3-D. Otherwise they go as
a TIFF in a per-job temp folder. Anything that does not fit comfortably in
RAM belongs in an OME-Zarr plus chunked batch/HPC workflow. Wavu deliberately
does not grow chunking, memory mapping or remote storage. That would
multiply the code and the support load, and other tools already do it well.

## D5: Token auth even on localhost

Other local users and browser pages can reach `127.0.0.1`. A random bearer
token, compared with `hmac.compare_digest`, keeps them from running scripts
through your worker. The token lives only in the parent process or in a
user-only handshake file.

## D6: Fiji client = Groovy scripts plus one library file loaded with `GroovyShell`

Wavu ships no jar, so there is no Maven or Java build. Every `.groovy` file
under `scripts/Plugins/` becomes a Fiji menu item, so the shared code lives
in `scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt`. No script language claims
the `.txt` extension, so ScriptFinder ignores the file. Each menu script
loads it with about 4 lines:
`new GroovyShell(this.class.classLoader).evaluate(file)`. That returns one
`WavuLib` object. Alternatives that were rejected:

- Duplicating the helpers in each script: the copies drift apart.
- A `.groovy` file on the classpath: this depends on Fiji's plugin
  classloader internals.
- A jar: needs a Java build (see D1).

`WAVU_LIB` overrides the path so tests can run the client straight from a
checkout. Live workers are kept in `System.getProperties()` under
`wavu.workers`, because that object survives between menu commands. Class
statics do not survive, since each evaluation defines a new class.

The client avoids Java 9+ APIs because the Fiji installation on the owner's
machine still runs **Java 8** (Zulu 8u452, ImageJ 1.54p, Groovy 4.0.23).
Current Fiji ships Java 21. Both should work.

## D7: pixi bootstrap downloads the archive, not the bare binary

pixi releases publish bare binaries, but `sha256.sum` only lists the
archives (`.zip` on Windows, `.tar.gz` elsewhere). The client therefore
downloads the archive and verifies its sha256 against `sha256.sum` from the
**same** release tag. It then extracts the binary with `java.util.zip` or a
roughly 20-line tar reader. The tag comes from the `releases/latest`
redirect. To pin a version, set the IJ preference `wavu.pixi.version`.

## D8: Version from the git tag only

hatch-vcs derives the Python package version from the tag. The Fiji library
carries an `@WAVU_VERSION@` placeholder, which `tools/make_fiji_zip.py` fills
in at release time. The client warns in the Log when its major.minor version
differs from the worker's.

## D9: Releases are driven from release-please, with no PAT

A tag created with `GITHUB_TOKEN` does not trigger other workflows.
`release-please.yml` therefore calls `release.yml` as a reusable workflow when
`release_created` is true. `release.yml` also accepts tag pushes and manual
dispatch. The jobs that need owner accounts are off by default and are
switched on with repository *variables*:

- Fiji update site: `FIJI_UPDATE_SITE=true`, plus the secrets
  `UPDATE_SITE_USER` and `UPDATE_SITE_PASS`.
- PyPI trusted publishing: `PYPI_PUBLISH=true`.

## D10: How a script environment gets wavu

- **Inside this repo** (the template and the examples): an editable path
  (`../..`), so they test the current code.
- **`wavu new-script` anywhere else** (the default): a git dependency,
  `wavu = { git = "https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu.git", tag = "vX.Y.Z" }`.
  Before the first release it uses `branch = "main"` instead of a tag. The
  owner chose this so scripts work before PyPI exists. **Trade-off:** pixi
  resolves git dependencies with the `git` command, so the developer's
  machine and CI need git. End users do not, as long as the shipped
  `pixi.lock` is used. `--wavu-source release`, which points at the release
  wheel URL and needs no git, or `--wavu-source pypi` avoid that.
- **`wavu package` refuses a path dependency**, because the path would not
  exist on users' machines.

## D11: GPL-3.0-or-later

This is the owner's choice. It is compatible with Fiji (GPL) and keeps
derivatives open.

## D12: Test data is BBBC039, committed

The tests use one BBBC039 image and its ground-truth mask (Broad Bioimage
Benchmark Collection; U2OS nuclei; licence CC0). Together they are 0.74 MB,
committed unmodified under `tests/data/BBBC039/`, so every CI run can use
real data without a network. `pixi run fetch-test-data` checks them by
sha256. An earlier draft used the Cell Tracking Challenge data, which was
dropped: its terms require permission for public non-challenge use and
forbid redistribution. See [test-data.md](test-data.md).

## D13: Distributing a script: `wavu package` and installed folders

A third-party script installs into `<Fiji.app>/wavu/scripts/<name>/`
(`script.py`, `pixi.toml`, `pixi.lock`, `README.md`). A menu stub of about 8
lines goes in `<Fiji.app>/scripts/Plugins/<Menu>/<Title>.groovy`. The stub
loads the Wavu library and calls `runScriptFolder(<that folder>)`. There is no
folder chooser. On first use, the environment is installed with
`pixi run --frozen`, which follows the shipped lock exactly. `wavu package`
builds this tree and a zip, and requires a `pixi.lock`. **Open question:** the
Fiji updater may not upload files outside its known top-level folders (`jars/`,
`plugins/`, `scripts/`, `macros/`, ...), and `wavu/` is not one of them. This
has not been verified against a real update site. If it fails, the fallback is
to move the folder under `scripts/` and give it extensions Fiji does not run.
