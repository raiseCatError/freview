"""Bounded, metadata-only discovery of existing specification artifacts.

Never reads spec contents, follows symlinks, or executes repository commands.
This inventory is a lead for an agent's later authorized evidence review, not
proof of a requirement or completed implementation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

SOURCES = {
    "openspec": (
        ("openspec/specs", "specification"),
        ("openspec/changes", "change"),
    ),
    "spec-kit": (
        ("specs", "specification"),
        (".specify", "framework"),
    ),
}
EXTENSIONS = frozenset({".md", ".yaml", ".yml", ".json"})
MAX_FILES = 200
MAX_DEPTH = 7
MAX_BYTES = 1_048_576


def discover(root: Path, *, max_files: int = MAX_FILES, max_depth: int = MAX_DEPTH) -> dict:
    if not 1 <= max_files <= MAX_FILES or not 1 <= max_depth <= MAX_DEPTH:
        raise ValueError("invalid discovery limits")
    root = Path(root).absolute()
    result = {"root": str(root), "artifacts": [], "truncated": False,
              "warnings": [], "status": "not-observed"}
    if root.is_symlink() or not root.is_dir():
        result["warnings"].append("root-unavailable-or-symlink")
        return result
    for provider, directories in SOURCES.items():
        for relative, role in directories:
            directory = root / relative
            if directory.is_symlink():
                result["warnings"].append("symlink-skipped:" + relative)
                continue
            if not directory.is_dir():
                continue
            stack = [(directory, 0)]
            while stack:
                current, depth = stack.pop()
                try:
                    with os.scandir(current) as scanned:
                        entries = sorted(scanned, key=lambda e: e.name)
                except OSError:
                    result["warnings"].append("unreadable-directory")
                    continue
                for entry in entries:
                    if len(result["artifacts"]) >= max_files:
                        result["truncated"] = True
                        break
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if depth + 1 < max_depth:
                                stack.append((Path(entry.path), depth + 1))
                            else:
                                result["truncated"] = True
                        elif entry.is_file(follow_symlinks=False):
                            path = Path(entry.path)
                            if path.suffix.lower() not in EXTENSIONS:
                                continue
                            size = entry.stat(follow_symlinks=False).st_size
                            if size > MAX_BYTES:
                                result["warnings"].append("oversized-artifact-skipped")
                                continue
                            result["artifacts"].append({
                                "provider": provider, "role": role,
                                "path": path.relative_to(root).as_posix(),
                                "size_bytes": size,
                                "evidence": "path-metadata-only",
                            })
                    except OSError:
                        result["warnings"].append("unreadable-entry")
                if result["truncated"] and len(result["artifacts"]) >= max_files:
                    break
    result["artifacts"].sort(key=lambda item: (item["provider"], item["path"]))
    result["status"] = "partial" if result["truncated"] or result["warnings"] else "inventory-only"
    if not result["artifacts"] and not result["warnings"] and not result["truncated"]:
        result["status"] = "no-known-artifacts"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--max-files", type=int, default=MAX_FILES)
    parser.add_argument("--max-depth", type=int, default=MAX_DEPTH)
    args = parser.parse_args()
    try:
        result = discover(args.root, max_files=args.max_files, max_depth=args.max_depth)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] not in ("not-observed",) else 2


if __name__ == "__main__":
    raise SystemExit(main())
