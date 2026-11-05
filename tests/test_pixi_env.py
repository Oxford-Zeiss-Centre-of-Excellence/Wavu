"""Launch mode 1 end to end, minus Fiji: `pixi run` a worker in the template's own env.

Slow the first time (installs the template environment); `pixi run test-integration`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

import numpy as np
import pytest

from wavu.codec import decode_array, encode_array

from conftest import REPO, Client

pytestmark = [pytest.mark.pixi_env, pytest.mark.timeout(1800)]


def test_template_worker_in_its_own_pixi_env():
    pixi = os.environ.get("PIXI_EXE") or shutil.which("pixi")
    if pixi is None:
        pytest.skip("pixi not on PATH")
    script_dir = REPO / "templates" / "wavu-script"
    proc = subprocess.Popen(
        [pixi, "run", "--manifest-path", str(script_dir / "pixi.toml"), "wavu-worker", "--script-dir", str(script_dir)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=script_dir,
    )
    try:
        hello = json.loads(proc.stdout.readline())
        client = Client(hello["port"], hello["token"])
        _, listing = client.get("/scripts")
        assert listing["scripts"]["script"]["params"]["sigma"]["default"] == 2.0
        img = np.zeros((16, 16), np.uint8)
        img[8, 8] = 200
        job = client.run("script", params={"sigma": 1.5}, inputs={"image": encode_array(img)})
        events = client.events(job)
        assert events[-1][0] == "done", events
        assert any(k == "progress" for k, _ in events)
        out = decode_array(client.get(f"/jobs/{job}/result")[1]["outputs"]["blurred"])
        assert out.dtype == np.uint8 and 0 < out[8, 8] < 200
    finally:
        proc.stdin.close()
        proc.wait(30)
        proc.stdout.close()
    assert proc.returncode == 0
