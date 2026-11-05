"""The agent instructions stay in one source: AGENTS.md must match SKILL.md."""

import subprocess
import sys

from conftest import REPO


def test_agents_md_is_generated_from_skill_md():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "make_agent_files.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_skill_has_the_frontmatter_agents_need():
    head = (REPO / "agent" / "skills" / "wavu" / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
    assert "name: wavu" in head and "description:" in head
