#!/usr/bin/env python3
"""Validate or compare freview JSON reports; standard library only, read-only."""
import argparse
import json
from pathlib import Path
import sys

KINDS = {"local-snapshot", "partial-audit", "full-audit"}
MODES = {"quick", "standard", "full", "targeted"}
SEVERITIES = {"P0", "P1", "P2", "informational"}
REQUIRED = {"schema_version", "generator", "report_kind", "timestamp_utc",
            "mode_requested", "scope", "repository", "findings", "not_observed"}


def load(path):
    raw = Path(path).read_bytes()
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("Report exceeds 16 MiB")
    report = json.loads(raw.decode("utf-8"))
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
    return repo.get("remote") or repo.get("root")


def compare(before, after):
    if identity(before) != identity(after):
        raise ValueError("Reports refer to different repositories")
    if before["report_kind"] != after["report_kind"]:
        raise ValueError("Cannot compare different report kinds without misleading status changes")
    if set(before["scope"]["included"]) != set(after["scope"]["included"]):
        raise ValueError("Cannot compare different category coverage")
    old = {x["id"]: x for x in before["findings"]}
    new = {x["id"]: x for x in after["findings"]}
    return {
        "kind": "freview-finding-delta/1",
        "repository": identity(after),
        "before": before["timestamp_utc"], "after": after["timestamp_utc"],
        "report_kind": after["report_kind"],
        "new": [new[x] for x in sorted(new.keys() - old.keys())],
        "resolved": [old[x] for x in sorted(old.keys() - new.keys())],
        "changed": [{"before": old[x], "after": new[x]}
                    for x in sorted(old.keys() & new.keys())
                    if any(old[x].get(k) != new[x].get(k)
                           for k in ("severity", "category", "summary", "status"))],
        "unchanged_count": sum(
            1 for x in old.keys() & new.keys()
            if all(old[x].get(k) == new[x].get(k)
                   for k in ("severity", "category", "summary", "status"))
        ),
        "warning": "Not observed/unverified gaps remain report-specific; a disappearance is not proof of a fix if evidence changed."
    }


def main():
    p = argparse.ArgumentParser(description="Validate or compare freview JSON reports")
    p.add_argument("reports", nargs="+", help="one report validates; two compare")
    p.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = p.parse_args()
    if len(args.reports) not in (1, 2):
        p.error("pass one report to validate, or two to compare")
    try:
        reports = [load(x) for x in args.reports]
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
                for heading in ("new", "resolved", "changed"):
                    print("## " + heading.title() + " (" + str(len(result[heading])) + ")")
                    for item in result[heading]:
                        f = item.get("after", item)
                        print("- " + str(f["id"]) + ": " + str(f["summary"]).replace("\n", " "))
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
