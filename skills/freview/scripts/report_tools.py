#!/usr/bin/env python3
"""Validate or compare freview JSON reports; standard library only, read-only."""
import argparse
import datetime as dt
import re
import json
import os
import unicodedata
from pathlib import Path
import sys

KINDS = {"local-snapshot", "partial-audit", "full-audit"}
MODES = {"quick", "standard", "full", "targeted"}
SEVERITIES = {"P0", "P1", "P2", "informational"}
REQUIRED = {"schema_version", "generator", "report_kind", "timestamp_utc",
            "mode_requested", "scope", "repository", "findings", "not_observed"}


def _matches_type(value, name):
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: type(value) is int,
        "number": lambda: type(value) in (int, float),
        "boolean": lambda: type(value) is bool,
        "null": lambda: value is None,
    }[name]()


def _validate(value, spec, root, location="$"):
    """Validate the JSON-Schema vocabulary actually used by report schema v1.

    Do not assert support for arbitrary third-party JSON Schemas.
    """
    if "$ref" in spec:
        ref = spec["$ref"]
        if not ref.startswith("#/"):
            raise ValueError("Unsupported external schema reference")
        target = root
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        return _validate(value, target, root, location)
    if "type" in spec:
        permitted = spec["type"]
        permitted = permitted if isinstance(permitted, list) else [permitted]
        if not any(_matches_type(value, kind) for kind in permitted):
            raise ValueError(location + ": invalid JSON type")
    if "enum" in spec and value not in spec["enum"]:
        raise ValueError(location + ": unsupported value")
    if "const" in spec and (type(value) is not type(spec["const"]) or value != spec["const"]):
        raise ValueError(location + ": invalid constant")
    if isinstance(value, dict):
        for key in spec.get("required", []):
            if key not in value:
                raise ValueError(location + ": missing required field " + key)
        props = spec.get("properties", {})
        for name, member in value.items():
            if name in props:
                _validate(member, props[name], root, location + "." + name)
            elif spec.get("additionalProperties") is False:
                raise ValueError(location + ": unexpected field " + name)
            elif isinstance(spec.get("additionalProperties"), dict):
                _validate(member, spec["additionalProperties"], root, location + "." + name)
    if isinstance(value, list):
        if len(value) < spec.get("minItems", 0) or len(value) > spec.get("maxItems", float("inf")):
            raise ValueError(location + ": invalid array length")
        if spec.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise ValueError(location + ": duplicate array elements")
        if isinstance(spec.get("items"), dict):
            for i, item in enumerate(value):
                _validate(item, spec["items"], root, location + "[" + str(i) + "]")
    if isinstance(value, str):
        if len(value) < spec.get("minLength", 0) or len(value) > spec.get("maxLength", float("inf")):
            raise ValueError(location + ": invalid string length")
        if "pattern" in spec and not re.search(spec["pattern"], value):
            raise ValueError(location + ": pattern mismatch")
        if spec.get("format") == "date-time":
            try:
                parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError()
            except ValueError:
                raise ValueError(location + ": invalid timezone-aware timestamp") from None
    if type(value) in (int, float):
        if value < spec.get("minimum", float("-inf")) or value > spec.get("maximum", float("inf")):
            raise ValueError(location + ": invalid numeric range")
    for condition in spec.get("allOf", []):
        if "if" in condition:
            try:
                _validate(value, condition["if"], root, location)
                passed = True
            except ValueError:
                passed = False
            if passed and "then" in condition:
                _validate(value, condition["then"], root, location)
        else:
            _validate(value, condition, root, location)


def load(path):
    # Open once, cap before parsing; reject symlinks where supported.
    max_bytes = 16 * 1024 * 1024
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("Report exceeds 16 MiB")
    report = json.loads(raw.decode("utf-8"))
    schema_file = Path(__file__).resolve().parents[1] / "assets/schemas/freview-report.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    _validate(report, schema, schema)
    if not isinstance(report, dict) or REQUIRED - set(report):
        raise ValueError("Missing top-level freview report keys")
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        raise ValueError("Unsupported report schema version")
    if report["report_kind"] not in KINDS or report["mode_requested"] not in MODES:
        raise ValueError("Invalid report kind or mode")
    scope, repo = report["scope"], report["repository"]
    if not isinstance(scope, dict) or not isinstance(repo, dict):
        raise ValueError("Invalid scope or repository")
    for key in ("included", "excluded"):
        if not isinstance(scope.get(key), list) or not all(isinstance(v, str) for v in scope[key]):
            raise ValueError("Invalid scope." + key)
    if not isinstance(report["not_observed"], list) or not all(isinstance(x, str) for x in report["not_observed"]):
        raise ValueError("Invalid not_observed")
    if report["report_kind"] in ("partial-audit", "full-audit"):
        if not scope["included"]:
            raise ValueError("Cannot claim audit without selected categories")
        for key in ("remediation_plan", "duplicate_clusters"):
            if not isinstance(report.get(key), list):
                raise ValueError("Agent audit must include " + key + " list")
        for action in report["remediation_plan"]:
            if (not isinstance(action, dict) or action.get("requires_approval") is not True or
                    not isinstance(action.get("verification"), list)):
                raise ValueError("Invalid non-executed repair action")
        for group in report["duplicate_clusters"]:
            if (not isinstance(group, dict) or
                    group.get("status") not in ("confirmed", "candidate", "related", "not-duplicate")):
                raise ValueError("Invalid duplicate cluster")
    if report["report_kind"] in ("partial-audit", "full-audit"):
        manifest = report["verification_manifest"]
        recorded = {}
        for entry in manifest:
            category = entry["category"]
            if category in recorded:
                raise ValueError("Duplicate evidence category: " + category)
            recorded[category] = entry
            if entry["status"] in ("verified", "not-applicable") and not entry["evidence"]:
                raise ValueError("Completed checks require evidence/reason: " + category)
        included = set(scope["included"])
        if not included <= recorded.keys():
            raise ValueError("Selected audit categories missing evidence manifest")
        if report["report_kind"] == "full-audit":
            for category in included:
                if recorded[category]["status"] not in ("verified", "not-applicable"):
                    raise ValueError("Cannot claim full-audit with incomplete " + category)
            if "code-review" in included and recorded["code-review"]["status"] != "verified":
                raise ValueError("Full code review must be evidenced, not skipped")
    if report["timestamp_utc"].endswith("Z"):
        pass
    else:
        when = dt.datetime.fromisoformat(report["timestamp_utc"])
        if when.utcoffset() != dt.timedelta(0):
            raise ValueError("timestamp_utc must use UTC, not a different offset")
    findings = report["findings"]
    if not isinstance(findings, list):
        raise ValueError("Findings must be an array")
    seen = set()
    for f in findings:
        if not isinstance(f, dict) or not all(k in f for k in ("id", "severity", "category", "summary", "status", "evidence")):
            raise ValueError("Malformed finding")
        if (not isinstance(f["id"], str) or not f["id"] or
            f["severity"] not in SEVERITIES or
            not isinstance(f["category"], str) or
            not isinstance(f["summary"], str) or
            not isinstance(f["status"], str) or
            not isinstance(f["evidence"], list) or
            not all(isinstance(x, str) for x in f["evidence"])):
            raise ValueError("Invalid finding fields")
        if f["id"] in seen:
            raise ValueError("Duplicate finding ID: " + f["id"])
        seen.add(f["id"])
    return report


def identity(report):
    repo = report["repository"]
    return repo.get("identity") or repo.get("remote") or repo.get("root")


def compare(before, after):
    first = identity(before)
    second = identity(after)
    if not first or not second:
        raise ValueError("Cannot compare reports without a stable repository identity")
    if first != second:
        raise ValueError("Reports refer to different repositories")
    if before["report_kind"] != after["report_kind"]:
        raise ValueError("Cannot compare different report kinds without misleading status changes")
    if (set(before["scope"]["included"]) != set(after["scope"]["included"]) or
            set(before["scope"]["excluded"]) != set(after["scope"]["excluded"]) or
            before["mode_requested"] != after["mode_requested"]):
        raise ValueError("Cannot compare different mode/category coverage")
    if (before["repository"].get("base_ref") != after["repository"].get("base_ref")):
        raise ValueError("Cannot compare reports based on different integration baselines")
    old = {x["id"]: x for x in before["findings"]}
    new = {x["id"]: x for x in after["findings"]}
    return {
        "kind": "freview-finding-delta/1",
        "repository": identity(after),
        "before": before["timestamp_utc"], "after": after["timestamp_utc"],
        "report_kind": after["report_kind"],
        "new": [new[x] for x in sorted(new.keys() - old.keys())],
        "absent_from_new_report": [old[x] for x in sorted(old.keys() - new.keys())],
        "changed": [{"before": old[x], "after": new[x]}
                    for x in sorted(old.keys() & new.keys())
                    if any(old[x].get(k) != new[x].get(k)
                           for k in ("severity", "category", "summary", "status"))],
        "unchanged_count": sum(
            1 for x in old.keys() & new.keys()
            if all(old[x].get(k) == new[x].get(k)
                   for k in ("severity", "category", "summary", "status"))
        ),
        "warning": "absent_from_new_report is NOT a verified fix. Validate each disappeared finding against the actual implementation and execution evidence."
    }


def safe_markdown(value):
    """Escape untrusted report text for terminal and Markdown presentation."""
    out = []
    for ch in str(value):
        cp = ord(ch)
        if unicodedata.category(ch) in ("Cc", "Cf", "Cs") or cp in (0x2028, 0x2029):
            out.append("\\u%04x" % cp if cp <= 0xFFFF else "\\U%08x" % cp)
        elif ch in "\\\\*_`[]()<>|":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def publication_risks(report):
    """Privacy heuristics only; passing never guarantees a safe public report."""
    patterns = (
        ("local-user-path", re.compile(r"(?:/Users/[^/\s]+|/home/[^/\s]+|/Volumes/[^/\s]+)")),
        ("file-uri", re.compile(r"file://", re.I)),
        ("url-userinfo", re.compile(r"\b(?:https?|ssh)://[^\s/@:]+:[^\s/@]+@", re.I)),
        ("credential-shaped-text", re.compile(r"\b(?:github_pat_|ghp_|gho_|sk-)[A-Za-z0-9_-]{12,}")),
        ("private-key-marker", re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE) PRIVATE KEY-----")),
    )
    found = set()

    def inspect(value):
        if isinstance(value, dict):
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
        elif isinstance(value, str):
            if any(unicodedata.category(ch) == "Cc" and ch not in "\r\n\t"
                   or ord(ch) in (0x202A, 0x202B, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069)
                   for ch in value):
                found.add("terminal-or-bidi-control")
            for label, regex in patterns:
                if regex.search(value):
                    found.add(label)

    inspect(report)
    return sorted(found)


def main():
    p = argparse.ArgumentParser(description="Validate or compare freview JSON reports")
    p.add_argument("reports", nargs="+", help="one report validates; two compare")
    p.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p.add_argument("--check-public", action="store_true",
                   help="advisory only: flag obvious private paths, token shapes and control text")
    args = p.parse_args()
    if len(args.reports) not in (1, 2):
        p.error("pass one report to validate, or two to compare")
    try:
        reports = [load(x) for x in args.reports]
        if args.check_public:
            if len(reports) != 1:
                raise ValueError("--check-public requires exactly one report")
            risks = publication_risks(reports[0])
            result = {"kind": "freview-publication-privacy-check/1",
                      "obvious_risks": risks,
                      "no_obvious_risks_detected": not risks,
                      "warning": "Heuristic check only: absence of matches does NOT certify publication safety. Manual review required."}
            print(json.dumps(result, indent=2) if args.format == "json" else
                  "Publication privacy check: " + (", ".join(risks) if risks else "no obvious patterns") +
                  "\\nManual privacy review always required.")
            return 3 if risks else 0
        if len(reports) == 1:
            result = {"valid": True, "kind": reports[0]["report_kind"],
                      "findings": len(reports[0]["findings"])}
            if args.format == "markdown":
                print("Valid freview report:", result)
                return 0
        else:
            result = compare(*reports)
            if args.format == "markdown":
                print("# freview report comparison\n")
                for heading in ("new", "absent_from_new_report", "changed"):
                    print("## " + heading.title() + " (" + str(len(result[heading])) + ")")
                    for item in result[heading]:
                        f = item.get("after", item)
                        print("- " + safe_markdown(f["id"]) + ": " + safe_markdown(f["summary"]))
                    print()
                print("Unchanged:", result["unchanged_count"])
                print(result["warning"])
                return 0
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print("freview: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
