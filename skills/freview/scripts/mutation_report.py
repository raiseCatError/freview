"""Bounded, read-only mutation quality evidence (Stryker and mutmut).

The report is untrusted metadata. Neither parsing nor a high mutation score
proves test quality, independence or correctness. No mutator is executed here.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

MAX_REPORT_BYTES = 2_097_152
MAX_MUTANTS = 10_000
MAX_FILES = 256
FORMATS = ("auto", "stryker", "mutmut")
STATUSES = {"Killed", "Timeout", "Survived", "NoCoverage",
            "CompileError", "RuntimeError", "Ignored", "Pending"}
DEFAULT_REPORTS = (("stryker", "reports/mutation/mutation.json"),
                   ("mutmut", "mutants/mutmut-cicd-stats.json"))


def _invalid(reason="invalid-report"):
    return {"status": "invalid", "reason_code": reason, "quality_pass": False,
            "source_format": None, "score": None, "survivors": [],
            "counts": {"detected": 0, "undetected": 0, "valid": 0}}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _safe_path(value):
    if not isinstance(value, str) or len(value) < 1 or len(value) > 512:
        return False
    if "\\" in value or any(ord(c) < 32 for c in value):
        return False
    p = PurePosixPath(value)
    return (not p.is_absolute() and
            all(part not in ("", ".", "..", ".git") for part in value.split("/")))


def _integer(value):
    return type(value) is int and value >= 0


def _sum_stryker(report, *, max_survivors):
    if (not isinstance(report.get("schemaVersion"), str) or
            not re.fullmatch(r"[12](?:\.\d+){0,2}", report["schemaVersion"]) or
            not isinstance(report.get("files"), dict) or
            not isinstance(report.get("thresholds"), dict) or
            len(report["files"]) > MAX_FILES):
        return _invalid()
    counts = {state: 0 for state in STATUSES}
    survivors = []
    seen = set()
    mutations = 0
    for path, entry in report["files"].items():
        if not _safe_path(path) or not isinstance(entry, dict) or not isinstance(entry.get("mutants"), list):
            return _invalid()
        for m in entry["mutants"]:
            mutations += 1
            if mutations > MAX_MUTANTS or not isinstance(m, dict):
                return _invalid("report-budget")
            state = m.get("status")
            ident = m.get("id")
            if not isinstance(state, str) or state not in STATUSES or not isinstance(ident, str):
                return _invalid("unknown-mutant-status")
            key = (path, ident)
            if key in seen:
                return _invalid("duplicate-mutant-id")
            seen.add(key)
            counts[state] += 1
            if state in ("Survived", "NoCoverage") and len(survivors) < max_survivors:
                location = m.get("location")
                start = location.get("start") if isinstance(location, dict) else None
                line = start.get("line") if isinstance(start, dict) else None
                line = line if _integer(line) and line > 0 else None
                survivors.append({"file": path, "id": ident[:80], "status": state,
                                  "line": line, "mutator": str(m.get("mutatorName", ""))[:80]})
    valid = counts["Killed"] + counts["Timeout"] + counts["Survived"] + counts["NoCoverage"]
    return {"status": "incomplete" if counts["Pending"] else "complete" if valid else "no-valid-mutants",
            "counts": {"detected": counts["Killed"] + counts["Timeout"],
                       "undetected": counts["Survived"] + counts["NoCoverage"],
                       "valid": valid, **counts}, "survivors": survivors,
            "source_format": "stryker"}


def _sum_mutmut(report):
    names = ("killed", "survived", "no_tests", "timeout", "skipped",
             "suspicious", "segfault", "check_was_interrupted_by_user", "total")
    if not all(name in report and _integer(report[name]) for name in names):
        return _invalid("invalid-mutmut-counts")
    if sum(report[name] for name in names if name != "total") != report["total"]:
        return _invalid("inconsistent-mutmut-total")
    valid = report["killed"] + report["timeout"] + report["survived"] + report["no_tests"]
    incomplete = any(report[key] > 0 for key in (
        "suspicious", "segfault", "check_was_interrupted_by_user"))
    return {
        "status": "incomplete" if incomplete else "complete" if valid else "no-valid-mutants",
        "counts": {"detected": report["killed"] + report["timeout"],
                   "undetected": report["survived"] + report["no_tests"],
                   "valid": valid, **{key: report[key] for key in names}},
        "survivors": [], "source_format": "mutmut"
    }


def summarize(report, *, format="auto", min_score=60, min_valid_mutants=1,
              max_survivors=12):
    if (format not in FORMATS or
            type(min_score) not in (int, float) or not 0 <= min_score <= 100 or
            type(min_valid_mutants) is not int or not 1 <= min_valid_mutants <= 10000 or
            type(max_survivors) is not int or not 0 <= max_survivors <= 50):
        return _invalid("invalid-options")
    if isinstance(report, bytes):
        if len(report) > MAX_REPORT_BYTES:
            return _invalid("report-budget")
        try:
            report = report.decode("utf-8")
        except UnicodeError:
            return _invalid()
    if isinstance(report, str):
        if len(report.encode("utf-8", errors="replace")) > MAX_REPORT_BYTES:
            return _invalid("report-budget")
        try:
            report = json.loads(report, object_pairs_hook=_pairs,
                                parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError, TypeError):
            return _invalid()
    if not isinstance(report, dict):
        return _invalid()
    if format == "auto":
        format = "stryker" if "schemaVersion" in report else "mutmut" if "killed" in report else "invalid"
    output = _sum_stryker(report, max_survivors=max_survivors) if format == "stryker" else _sum_mutmut(report) if format == "mutmut" else _invalid()
    if output["status"] == "invalid":
        return output
    valid = output["counts"]["valid"]
    detected = output["counts"]["detected"]
    output["score"] = round(100 * detected / valid, 2) if valid else None
    output["quality_pass"] = (output["status"] == "complete" and valid >= min_valid_mutants and
                              output["score"] is not None and output["score"] >= min_score)
    output["threshold"] = min_score
    output["min_valid_mutants"] = min_valid_mutants
    output["untrusted_metadata"] = True
    output["proves_test_quality"] = False
    return output


def inspect_workspace(workspace: Path, *, format="auto", min_score=60,
                      min_valid_mutants=1, max_survivors=12):
    workspace = Path(workspace)
    if workspace.is_symlink() or not workspace.is_dir():
        return _invalid("workspace-unavailable")
    candidates = [(fmt, relative) for fmt, relative in DEFAULT_REPORTS
                  if format in ("auto", fmt)]
    found = []
    for fmt, relative in candidates:
        cursor = workspace
        for component in PurePosixPath(relative).parts:
            cursor = cursor / component
            if cursor.is_symlink():
                return _invalid("symlink-report-path")
        if cursor.exists():
            found.append((fmt, cursor))
    if len(found) != 1:
        return _invalid("missing-or-ambiguous-report") if found else {
            **_invalid("missing-report"), "status": "missing"}
    fmt, path = found[0]
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        with os.fdopen(os.open(path, flags), "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                return _invalid("nonregular-report")
            raw = handle.read(MAX_REPORT_BYTES + 1)
    except OSError:
        return _invalid("report-unreadable")
    result = summarize(raw, format=fmt, min_score=min_score,
                       min_valid_mutants=min_valid_mutants, max_survivors=max_survivors)
    result["report_path"] = str(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--format", choices=FORMATS, default="auto")
    parser.add_argument("--min-score", type=float, default=60)
    args = parser.parse_args()
    file = args.report
    if file.is_symlink() or not file.is_file() or file.stat().st_size > MAX_REPORT_BYTES:
        print(json.dumps(_invalid("unavailable")))
        return 2
    output = summarize(file.read_bytes(), format=args.format, min_score=args.min_score)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
