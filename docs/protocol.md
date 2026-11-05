# Worker protocol

`wavu-worker --script-dir <dir>` serves one script folder. The source is
`src/wavu/worker.py`, which uses only the standard library.

## Start-up

- The worker binds `127.0.0.1` on a random free port. Override with `--host`
  and `--port`. Use `--host 0.0.0.0` only inside a container.
- It prints **exactly one JSON line** to stdout:
  `{"wavu": "<version>", "port": N, "token": "<random>"}`. After that, stdout
  goes to stderr, or to the running job's log when a script prints.
- `--handshake-file [PATH]` writes the same information, plus `pid`, `host`,
  `script_dir` and `tmp_dir`, to a JSON file. The default path is
  `~/.wavu/worker.json`. The file is removed on exit.
- The token comes from `--token`, or `$WAVU_TOKEN`, or is generated at random.
- **Lifetime:** the worker exits when its stdin closes, which happens when
  the parent (Fiji) dies. It also exits on `POST /shutdown`. With
  `--detached`, closing stdin is ignored; use that for terminal and container
  modes.
- `--debugpy PORT [--debugpy-wait]` starts debugpy so VS Code can attach.

## Requests

Every request needs `Authorization: Bearer <token>`. Without it, the worker
answers `401 {"error": ...}`.

| method | path | body | response |
|---|---|---|---|
| GET | `/health` | | `{"ok": true, "wavu": v, "scripts": n, "script_dir": ...}` |
| GET | `/scripts` | | `{"scripts": {name: {"name", "doc", "params"}}, "errors": {name: msg}}` |
| POST | `/run` | `{"script", "params", "inputs", "inline_limit"?}` | `{"job": id}`, or `400 {"error"}` for an unknown script, bad params or bad inputs |
| GET | `/jobs/<id>/events[?since=N]` | | `text/event-stream` (below) |
| POST | `/jobs/<id>/cancel` | | `{"ok": true, "status"}` |
| GET | `/jobs/<id>/result` | | `{"status": "done", "outputs"}`, `{"status": "error", "error"}` or `{"status": "cancelled"}`. `409` while the job is running. |
| POST | `/shutdown` | | `{"ok": true}`, then the worker exits |

An entry in `inputs` is either inline,
`{"dtype", "shape", "data": base64 little-endian, "meta"}`, or a file,
`{"path", "meta"}`.

## Events

```
id: 3
event: progress
data: {"value": 0.5}
```

Event kinds are `log` (`{"message"}`), `progress` (`{"value"}`), then exactly
one terminal event: `done` (`{"outputs": [names]}`), `error` (`{"message",
"traceback"}`) or `cancelled`. The stream closes after the terminal event. A
`: keepalive` comment is sent every 15 s. To resume a stream, reconnect with
`?since=<number of events already seen>`.

## Outputs

Each output has a `kind`: `image` (inline `data`, or a `path` to an ImageJ
TIFF), `table` (`path` to a CSV, plus `columns`), `rois` (`path`), `file`
(`path`) or `value` (`value`).
