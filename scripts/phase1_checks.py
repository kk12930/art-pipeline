from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_check(command: list[str], cwd: Path) -> None:
    print(f"Running: {' '.join(command)}")
    _ = subprocess.check_call(command, cwd=cwd)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    python = sys.executable

    checks = [
        [python, "-m", "unittest", "discover", "-v"],
        [python, "-m", "unittest", "tests.test_generate_sdxl", "-v"],
        [python, "-m", "unittest", "tests.test_api", "-v"],
        [python, "scripts/generate_sdxl.py", "--help"],
    ]

    for command in checks:
        run_check(command, repo_root)

    print("Phase 1 lightweight checks completed.")


if __name__ == "__main__":
    main()
