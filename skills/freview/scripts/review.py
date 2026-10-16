#!/usr/bin/env python3
"""freview config-aware local snapshot. Read-only unless --output explicitly selects a new file."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True  # Avoid creating __pycache__ during an audit.
from repo_snapshot import snapshot, text

CATEGORIES = ("git", "tracking", "implementation", "ci", "releases", "docs",
              "community", "dependencies", "security-posture", "accessibility",
              "code-review", "security-scan")
CORE = CATEGORIES[:10]
QUICK = ("git", "ci", "releases", "docs", "community")
SECTIONS = {
    "repository": {"project_type", "development_branch", "release_branches"},
    "defaults": {"mode", "include", "exclude"},
    "limits": {"max_branches", "max_issues", "max_prs"},
    "specialists": {"code_review", "security_scan", "repository_lint"},
    "acceptance": {"human_qa_required", "notes"},
}
SPECIALIST_VALUES = {
    "code_review": {"prefer-installed", "native-only", "ask", "off"},
    "security_scan": {"prefer-installed", "ask", "off"},
    "repository_lint": {"prefer-installed", "ask", "off"},
}


def check_str_list(value, key, max_count, max_length, choices=None):
    if (not isinstance(value, list) or len(value) > max_count or
        any(not isinstance(x, str) or not (1 <= len(x) <= max_length) or
            (choices is not None and x not in choices) for x in value) or
        len(set(value)) != len(value)):
        raise ValueError(key + " must be a bounded unique list of allowed strings")


def load_policy(path):
    if not path.is_file():
        raise ValueError("Config file not found: " + str(path))
    if path.stat().st_size > 65536:
        raise ValueError("Config exceeds 64 KiB")
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid config JSON: " + str(exc)) from exc
    if not isinstance(policy, dict) or set(policy) - {"schema_version", *SECTIONS}:
        raise ValueError("Unexpected top-level config keys")
    if type(policy.get("schema_version")) is not int or policy["schema_version"] != 1:
        raise ValueError("Unsupported config schema_version; expected integer 1")
    for section, keys in SECTIONS.items():
        part = policy.get(section, {})
        if not isinstance(part, dict) or set(part) - keys:
            raise ValueError("Invalid keys or section type in " + section)
        for name, value in part.items():
            key = section + "." + name
            if section == "repository":
                if name == "release_branches":
                    check_str_list(value, key, 30, 200)
                elif not isinstance(value, str) or not (1 <= len(value) <= 200):
                    raise ValueError(key + " must be bounded text")
                elif any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
                    raise ValueError(key + " contains control characters")
            elif section == "defaults":
                if name == "mode" and value not in ("quick", "standard", "full"):
                    raise ValueError(key + " invalid mode")
                if name in ("include", "exclude"):
                    check_str_list(value, key, 12, 40, CATEGORIES)
            elif section == "limits":
                cap = 2000 if name == "max_branches" else 5000
                if type(value) is not int or not (1 <= value <= cap):
                    raise ValueError(key + " out of range")
            elif section == "specialists":
                if not isinstance(value, str) or value not in SPECIALIST_VALUES[name]:
                    raise ValueError(key + " invalid specialist preference")
            elif section == "acceptance":
                if name == "human_qa_required" and type(value) is not bool:
                    raise ValueError(key + " must be boolean")
                if name == "notes":
                    check_str_list(value, key, 20, 300)
    return policy


def categories(items):
    out = []
    for item in items:
        for token in item.split(","):
            name = token.strip().lower().replace("_", "-").replace(" ", "-")
            if name not in CATEGORIES:
                raise ValueError("Unknown review category: " + name)
            if name not in out:
                out.append(name)
    return out


def scope(args, config):
    prefs = config.get("defaults", {})
    mode = args.mode or prefs.get("mode", "standard")
    selected = list(QUICK if mode == "quick" else CORE)
    if mode == "full":
        selected.append("code-review")
    for name in prefs.get("include", []):
        if name not in selected:
            selected.append(name)
    only = categories(args.only)
    if only:
        selected = only
    with_categories = categories(args.with_categories)
    for name in with_categories:
        if name not in selected:
            selected.append(name)
    excluded = set(prefs.get("exclude", []))
    specialist = config.get("specialists", {})
    explicit_code = ("code-review" in with_categories or "code-review" in only
                     or args.mode == "full")
    # Standard/quick are code-free unless user explicitly requests code review.
    if mode != "full" and not explicit_code:
        excluded.add("code-review")
    if specialist.get("code_review") == "off" and not explicit_code:
        excluded.add("code-review")
    if explicit_code:
        excluded.discard("code-review")
    if specialist.get("security_scan") == "off":
        excluded.add("security-scan")
    excluded -= set(with_categories)
    excluded.update(categories(args.exclude))
    return mode, [x for x in selected if x not in excluded], sorted(excluded)


def create_report(args):
    root_value = text(["rev-parse", "--show-toplevel"])
    if not root_value:
        raise ValueError("Not inside a Git repository")
    root = Path(root_value)
    cfgpath = Path(args.config).expanduser() if args.config else root / ".freview.json"
    cfg = load_policy(cfgpath) if cfgpath.exists() or args.config else {}
    mode, included, excluded = scope(args, cfg)
    base = args.base or cfg.get("repository", {}).get("development_branch")
    snap = snapshot(base, cfg.get("limits", {}).get("max_branches", 200))
    findings = []
    if not snap["status"]["clean"] and "git" in included:
        findings.append({
            "id": "local-working-tree-changes", "severity": "informational",
            "category": "git", "summary": "Current worktree has local changes; no cleanup is implied",
            "status": "observed", "evidence": ["git status --porcelain=v1 -z"],
            "next_action": "Ask branch/worktree owner before changing files"
        })
    if snap["npm_root_alignment"].get("status") == "drift" and "dependencies" in included:
        findings.append({
            "id": "npm-root-lock-drift", "severity": "P1", "category": "dependencies",
            "summary": "Root npm manifest/lock declarations disagree", "status": "observed",
            "evidence": ["package.json", "package-lock.json"],
            "next_action": "Review the drift; never regenerate a lockfile automatically"
        })
    # These steps are recommendations, never automatically executed.
    proposed = []
    for finding in findings:
        if finding["id"] == "npm-root-lock-drift":
            steps = ["Identify which manifest or lockfile reflects intended direct dependencies",
                     "Reconcile only after developer approval in a separate change"]
            verification = ["Check ecosystem-native lock consistency and approved CI"]
        else:
            steps = ["Identify the owner and purpose of each local change before any cleanup"]
            verification = ["Confirm intended worktree state with its owner"]
        finding["remediation"] = {
            "summary": finding["next_action"], "steps": steps,
            "verification": verification, "confidence": "medium",
            "requires_approval": True
        }
        proposed.append({
            "finding_ids": [finding["id"]], "action": finding["next_action"],
            "priority": finding["severity"], "verification": verification,
            "requires_approval": True
        })
    unobserved = [
        "Local-only structural snapshot, not a completed AI or remote repository audit.",
        "Hosted issues/PRs, CI jobs, releases, deployments and security alerts not fetched.",
        "Feature reachability, code review and physical accessibility were not verified.",
        "Uncommitted state of other worktrees and remote freshness were not inspected."
    ]
    if "code-review" in included:
        unobserved.append("Code review is selected but requires an agent/specialist; helper did not run one.")
    if "security-scan" in included:
        unobserved.append("Security scan selected but not executed by helper.")
    report = {
        "schema_version": 1, "generator": "freview-local/1",
        "report_kind": "local-snapshot", "timestamp_utc": snap["collected_utc"],
        "mode_requested": mode, "scope": {
            "included": included, "excluded": excluded,
            "specialists": {x: ("agent-review-required" if x in included else "not-selected")
                            for x in ("code-review", "security-scan")},
            "coverage": "local Git and root-level metadata only"
        },
        "repository": {"root": snap["root"], "remote": None,
                       "base_ref": snap["base"]["ref"] if snap["base"] else None,
                       "base_sha": snap["base"]["sha"] if snap["base"] else None,
                       "head_sha": snap["head_sha"]},
        "findings": findings, "not_observed": unobserved, "local_snapshot": snap,
        "human_review_required": cfg.get("acceptance", {}).get("human_qa_required", False),
        "reference_report": None,
        "duplicate_clusters": [],
        "remediation_plan": proposed,
        "implementation_suggestions_requested": bool(args.suggest_implementation)
    }
    return report, cfgpath if cfg else None


def markdown(report, config_path):
    def safe(value):
        return str(value).replace(chr(96), "'").replace("\n", " ")
    lines = [
        "# freview — local-only snapshot", "",
        "- Collected: " + safe(report["timestamp_utc"]),
        "- Mode requested: " + safe(report["mode_requested"]),
        "- Report kind: local-snapshot (not a complete audit)",
        "- Repository: " + safe(report["repository"]["root"]),
        "- HEAD: " + safe(report["repository"]["head_sha"]),
        "- Project config: " + (safe(config_path) if config_path else "none"),
        "- Included: " + ", ".join(report["scope"]["included"]),
        "", "## Observations", ""
    ]
    if report["findings"]:
        lines.extend("- " + safe(f["severity"]) + ": " + safe(f["summary"])
                     for f in report["findings"])
    else:
        lines.append("No findings in the selected local checks; other gates are not reviewed.")
    lines.extend(["", "## Not observed", ""])
    lines.extend("- " + safe(x) for x in report["not_observed"])
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="freview read-only local metadata")
    ap.add_argument("--mode", choices=("quick", "standard", "full"))
    ap.add_argument("--base")
    ap.add_argument("--config", help="project config; auto-detected from root if present")
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--with", dest="with_categories", action="append", default=[])
    ap.add_argument("--suggest-implementation", action="store_true", help="Request future feature ideas from an agent; local helper does not generate them")
    ap.add_argument("--format", choices=("json", "markdown"), default="markdown")
    ap.add_argument("--output", help="explicit output path; stdout is default (no file writes)")
    args = ap.parse_args()
    try:
        report, cfgpath = create_report(args)
        output = (json.dumps(report, indent=2) + "\n"
                  if args.format == "json" else markdown(report, cfgpath))
        if args.output:
            dest = Path(args.output).expanduser()
            if not dest.parent.is_dir():
                raise ValueError("Output parent doesn't exist; no directories are created")
            with dest.open("x", encoding="utf-8") as stream:
                stream.write(output)
            print("Wrote local snapshot: " + str(dest))
        else:
            print(output, end="")
    except (ValueError, RuntimeError, OSError) as exc:
        print("freview: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
