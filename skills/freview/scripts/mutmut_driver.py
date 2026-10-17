#!/usr/bin/env python3
"""Optional trusted mutmut adapter: run mutations, then export CI stats.

Use only as an explicitly configured freview ops mutation argv. mutmut itself
must already be installed. The parent freview ops process imposes isolation,
output and process-group budgets; this adapter provides its own timeout.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", default="mutmut", help="already installed mutmut CLI")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 600:
        parser.error("timeout must be between 1 and 600 seconds")
    if not args.binary or "\0" in args.binary or "\n" in args.binary:
        parser.error("invalid binary")
    # This adapter neither evaluates shell strings nor installs dependencies.
    for operation in ("run", "export-cicd-stats"):
        try:
            result = subprocess.run([args.binary, operation], timeout=args.timeout_seconds,
                                    check=False)
        except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
            return 2
        if result.returncode != 0:
            return 2
    target = Path("mutants/mutmut-cicd-stats.json")
    try:
        if target.is_symlink() or not stat.S_ISREG(target.stat().st_mode):
            return 2
        if target.stat().st_size == 0:
            return 2
    except OSError:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
