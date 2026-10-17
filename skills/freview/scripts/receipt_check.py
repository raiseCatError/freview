"""Validate bounded, untrusted verification receipts without running commands.

Receipt validation checks consistency and evidence *descriptions*, not authenticity.
Never label a receipt as independently reproduced just because its author says so.
"""
from __future__ import annotations

import argparse
import json
import re
import os
import stat
from pathlib import Path

MAX_BYTES = 131_072
MAX_CHECKS = 64
SHA = re.compile(r"^[0-9a-f]{40}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,100}$")
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
KINDS = {"worker", "independent", "ci"}
MAX_EVIDENCE = 8


def validate(receipt: object, *, expected_sha: str | None = None) -> dict:
    """Return a diagnostic; never imply that untrusted receipt claims are true."""
    errors = []
    warnings = []
    if not isinstance(receipt, dict):
        return {"status": "invalid", "errors": ["receipt-not-an-object"], "warnings": []}
    if expected_sha is not None and not SHA.fullmatch(expected_sha):
        raise ValueError("expected SHA must be a lowercase full 40-character Git SHA")
    if set(receipt) - {"schema_version", "repository", "head_sha", "checks"}:
        errors.append("unknown-receipt-fields")
    if receipt.get("schema_version") != 1:
        errors.append("unsupported-schema-version")
    repo = receipt.get("repository")
    if not isinstance(repo, str) or not REPO_NAME.fullmatch(repo) or ".." in repo:
        errors.append("invalid-repository")
    sha = receipt.get("head_sha")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        errors.append("invalid-head-sha")
    elif expected_sha is not None and sha != expected_sha:
        errors.append("unexpected-head-sha")
    checks = receipt.get("checks")
    if not isinstance(checks, list) or not (1 <= len(checks) <= MAX_CHECKS):
        errors.append("invalid-check-count")
        checks = []
    seen = set()
    checked = []
    for number, item in enumerate(checks):
        prefix = f"check-{number}:"
        if not isinstance(item, dict):
            errors.append(prefix + "invalid-object")
            continue
        if set(item) - {"id", "actor", "sha", "command", "exit_code", "evidence", "suite", "note"}:
            errors.append(prefix + "unknown-fields")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not SAFE_ID.fullmatch(identifier):
            errors.append(prefix + "invalid-id")
        elif identifier in seen:
            errors.append(prefix + "duplicate-id")
        else:
            seen.add(identifier)
        actor = item.get("actor")
        if actor not in KINDS:
            errors.append(prefix + "invalid-actor")
        itemsha = item.get("sha")
        if not isinstance(itemsha, str) or not SHA.fullmatch(itemsha):
            errors.append(prefix + "invalid-sha")
        elif isinstance(sha, str) and itemsha != sha:
            errors.append(prefix + "mismatched-check-sha")
        command = item.get("command")
        if not isinstance(command, str) or not command.strip() or len(command) > 2048:
            errors.append(prefix + "missing-or-invalid-command")
        code = item.get("exit_code")
        if not isinstance(code, int) or isinstance(code, bool) or not -255 <= code <= 255:
            errors.append(prefix + "invalid-exit-code")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or len(evidence) > MAX_EVIDENCE or any(
            not isinstance(e, str) or not e.strip() or len(e) > 512 for e in evidence
        ):
            errors.append(prefix + "invalid-evidence")
        elif not evidence:
            warnings.append(prefix + "no-artifact-or-run-reference")
        if actor == "independent":
            warnings.append(prefix + "independence-claimed-not-proven")
        if code is not None and type(code) is int and code != 0:
            warnings.append(prefix + "nonzero-exit")
        checked.append({"id": identifier if isinstance(identifier, str) else None,
                        "actor_claimed": actor if actor in KINDS else None,
                        "reported_exit_code": code if type(code) is int else None})
    mismatch = any("unexpected-head-sha" in e or "mismatched-check-sha" in e for e in errors)
    red = any("nonzero-exit" in w for w in warnings)
    incomplete = any("no-artifact-or-run-reference" in w for w in warnings)
    status = ("contradictory" if mismatch else "invalid" if errors
              else "failed" if red else "incomplete" if incomplete
              else "claimed-evidence")
    # Consistency, never trust provenance: a valid receipt cannot establish
    # that a command ran or that the actor was independent.
    return {"status": status, "errors": errors, "warnings": warnings,
            "checks": checked, "provenance_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path, help="JSON receipt to inspect, without executing commands")
    parser.add_argument("--expected-sha", help="exact lowercase 40-character Git SHA")
    args = parser.parse_args()
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        if args.receipt.is_symlink():
            raise ValueError("receipt is a symlink")
        fd = os.open(args.receipt, flags)
        with os.fdopen(fd, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError("receipt is not a regular file")
            raw = source.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("receipt exceeds byte limit")
        receipt = json.loads(raw.decode("utf-8"))
        result = validate(receipt, expected_sha=args.expected_sha)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
        # Avoid echoing arbitrary secret-bearing file paths or contents.
        print(json.dumps({"status": "invalid", "errors": ["unreadable-or-invalid-receipt"],
                          "provenance_verified": False}))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "claimed-evidence" else 2


if __name__ == "__main__":
    raise SystemExit(main())
