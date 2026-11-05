"""Build the agent files from the one source, agent/skills/wavu/SKILL.md.

    python tools/make_agent_files.py           # write agent/AGENTS.md and guide/assets/agent/wavu-skill.zip
    python tools/make_agent_files.py --check   # fail if agent/AGENTS.md is out of date (used by the tests)

AGENTS.md (Codex, OpenCode, Gemini CLI, Cursor, Copilot...) is SKILL.md without its
frontmatter. The zip (claude.ai / Claude Desktop "upload skill") is built at docs-build
time and not committed.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "agent" / "skills" / "wavu" / "SKILL.md"
AGENTS = REPO / "agent" / "AGENTS.md"
ZIP = REPO / "guide" / "assets" / "agent" / "wavu-skill.zip"
HEADER = (
    "<!-- Generated from agent/skills/wavu/SKILL.md by tools/make_agent_files.py; edit that file instead. -->\n"
    "<!-- Wavu agent instructions: https://oxford-zeiss-centre-of-excellence.github.io/Wavu/agents/ -->\n\n"
)


def agents_text() -> str:
    text = SKILL.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2].lstrip("\n")
    return HEADER + text


def main(argv: list[str]) -> int:
    want = agents_text()
    if "--check" in argv:
        have = AGENTS.read_text(encoding="utf-8") if AGENTS.exists() else ""
        if have.replace("\r\n", "\n") != want:
            print("agent/AGENTS.md is out of date: run python tools/make_agent_files.py")
            return 1
        return 0
    AGENTS.write_text(want, encoding="utf-8", newline="\n")
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(SKILL, "wavu/SKILL.md")
    print(f"wrote {AGENTS.relative_to(REPO)} and {ZIP.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
