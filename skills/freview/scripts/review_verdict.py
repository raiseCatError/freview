"""Bounded, strict review-verdict decoder.

A process exit code or JSON reply is not an independent verification attestation.
The caller MUST independently tie the report to the observed source and workspace.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import re

MAX_BYTES = 16384
MAX_FINDINGS = 24
MAX_PATHS = 32
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
VERDICTS = {"approve", "changes_requested", "blocked"}
SEVERITIES = {"critical", "high", "medium", "low", "info"}


class _DuplicateKey(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKey()
        value[key] = item
    return value


def _invalid(reason: str = "invalid-review-receipt") -> dict:
    # No untrusted prompt/paths/content are echoed in validation errors.
    return {"status": "invalid", "reason_code": reason,
            "findings": [], "reviewer_independence_verified": False,
            "source_reading_verified": False, "test_quality_verified": False}


def _path_ok(value: object) -> bool:
    if not isinstance(value, str) or not (1 <= len(value) <= 512):
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    path = PurePosixPath(value)
    if (path.is_absolute() or value.startswith("\\") or
            "\\" in value or ":" in value.split("/")[0] or
            any(part in ("", ".", "..", ".git") for part in value.split("/"))):
        return False
    return True


def validate(payload: bytes | str | dict, *, expected_sha: str,
             expected_digest: str) -> dict:
    """Report a *claimed* review, never a proof of reviewer independence.

    Invalid or contradictory input fails closed. Exact SHA and workspace
    digest are established by the runner and supplied separately, never copied
    from the reviewer's self-description.
    """
    if not isinstance(expected_sha, str) or not SHA.fullmatch(expected_sha):
        return _invalid("invalid-expected-sha")
    if not isinstance(expected_digest, str) or not DIGEST.fullmatch(expected_digest):
        return _invalid("invalid-expected-digest")
    if isinstance(payload, bytes):
        if len(payload) > MAX_BYTES:
            return _invalid("receipt-too-large")
        try:
            payload = payload.decode("utf-8", errors="strict")
        except UnicodeError:
            return _invalid()
    if isinstance(payload, str):
        if len(payload.encode("utf-8", errors="replace")) > MAX_BYTES:
            return _invalid("receipt-too-large")
        try:
            payload = json.loads(payload, object_pairs_hook=_strict_object,
                                 parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
        except (ValueError, TypeError):
            return _invalid()
    if not isinstance(payload, dict):
        return _invalid()
    allowed = {"schema_version", "source_sha", "workspace_digest",
               "verdict", "findings", "reviewed_paths", "reason"}
    if set(payload) != allowed:
        return _invalid("missing-or-unknown-fields")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        return _invalid("unsupported-version")
    sha = payload["source_sha"]
    digest = payload["workspace_digest"]
    if not isinstance(sha, str) or not SHA.fullmatch(sha) or sha != expected_sha:
        return _invalid("source-sha-mismatch")
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest) or digest != expected_digest:
        return _invalid("workspace-digest-mismatch")
    verdict = payload["verdict"]
    if not isinstance(verdict, str) or verdict not in VERDICTS:
        return _invalid("invalid-verdict")
    reason = payload["reason"]
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 500:
        return _invalid("invalid-reason")
    paths = payload["reviewed_paths"]
    if (not isinstance(paths, list) or not 1 <= len(paths) <= MAX_PATHS or
            not all(_path_ok(path) for path in paths) or len(set(paths)) != len(paths)):
        return _invalid("invalid-reviewed-paths")
    findings = payload["findings"]
    if not isinstance(findings, list) or len(findings) > MAX_FINDINGS:
        return _invalid("invalid-findings")
    known_ids: set[str] = set()
    cleaned = []
    for item in findings:
        if not isinstance(item, dict) or set(item) != {
                "id", "severity", "path", "description", "evidence"}:
            return _invalid("invalid-finding")
        item_id = item["id"]
        if not isinstance(item_id, str) or not IDENT.fullmatch(item_id) or item_id in known_ids:
            return _invalid("duplicate-or-invalid-finding-id")
        known_ids.add(item_id)
        if item["severity"] not in SEVERITIES if isinstance(item["severity"], str) else True:
            return _invalid("invalid-severity")
        if not _path_ok(item["path"]):
            return _invalid("invalid-finding-path")
        if not all(isinstance(item[key], str) and
                   1 <= len(item[key].strip()) <= bound for key, bound in
                   (("description", 500), ("evidence", 800))):
            return _invalid("invalid-finding-text")
        cleaned.append(dict(item))
    if verdict == "approve" and findings:
        return _invalid("approved-with-findings")
    if verdict == "changes_requested" and not findings:
        return _invalid("changes-requested-without-findings")
    status = {"approve": "approved-claim",
              "changes_requested": "changes-requested",
              "blocked": "blocked"}[verdict]
    return {"status": status, "reason": reason, "source_sha": sha,
            "workspace_digest": digest, "reviewed_paths": list(paths),
            "findings": cleaned, "reviewer_independence_verified": False,
            "source_reading_verified": False, "test_quality_verified": False}
