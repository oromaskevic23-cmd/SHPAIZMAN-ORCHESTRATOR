"""Check project identity and guard against deletion of third-party notices."""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import subprocess


def main():
    lead = "Alexander Viktorovich Negriy"
    for name in ("AUTHORS.md", "README.md"):
        if lead not in Path(name).read_text(encoding="utf-8"):
            raise SystemExit("PROJECT_LEAD_MISSING: " + name)
    authors = Path("AUTHORS.md").read_text(encoding="utf-8")
    for phrase in ("Git commit authors", "third-party copyright notices"):
        if phrase not in authors:
            raise SystemExit("PROVENANCE_SAFEGUARD_MISSING")
    for name in ("LICENSE", ".github/CODEOWNERS"):
        if not Path(name).is_file():
            raise SystemExit("REQUIRED_NOTICE_MISSING: " + name)

    base = os.environ.get("BASE_SHA", "").strip()
    if base and base != "0" * 40:
        if not re.fullmatch(r"[a-fA-F0-9]{40}", base):
            raise SystemExit("INVALID_BASE_SHA")
        diff = subprocess.run(
            ["git", "diff", "--name-status", "--find-renames", base, "HEAD", "--"],
            check=True, capture_output=True, text=True,
        )
        for line in diff.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 2 or not parts[0].startswith(("D", "R")):
                continue
            old = parts[1]
            name = PurePosixPath(old).name.upper()
            if (old in {"AUTHORS.md", ".github/CODEOWNERS"}
                    or name.startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE"))):
                raise SystemExit("NOTICE_REMOVED_OR_MOVED: " + old)
    print("Project identity and tracked notice-deletion checks passed.")
    print("Not a complete license audit or copyright ownership determination.")


if __name__ == "__main__":
    main()
