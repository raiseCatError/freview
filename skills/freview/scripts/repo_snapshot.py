#!/usr/bin/env python3
"""freview local snapshot: read-only Git and filesystem metadata, Python stdlib only.

Does not fetch, install, execute project code, alter branches or delete files.
This complements (does not replace) the agent's forge/CI and implementation review.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys


def git(args, cwd=None, allowed_failure=False):
    env = os.environ.copy()
    # Git's fsmonitor setting can execute arbitrary local programs even for
    # 'git status'. Force off at invocation time; do not trust repository config.
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    try:
        p = subprocess.run(
            ["git", "--no-optional-locks",
             "-c", "core.fsmonitor=false",
             "-c", "core.hooksPath=" + os.devnull,
             "-c", "diff.external=",
             "-c", "core.pager=cat",
             *args], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        if allowed_failure:
            return None
        raise RuntimeError(f"Git could not run: {exc}") from exc
    if p.returncode and not allowed_failure:
        msg = p.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"git {args[0]} failed ({p.returncode}): {msg[:350]}")
    return p.stdout if p.returncode == 0 else None


def text(args, cwd=None, allowed_failure=False):
    out = git(args, cwd, allowed_failure)
    return out.decode("utf-8", "replace").strip() if out is not None else None


def commit(ref, root):
    return text(["rev-parse", "--verify", "--quiet", ref + "^{commit}"], root, True)


def divergence(base, head, root):
    raw = text(["rev-list", "--left-right", "--count", base + "..." + head], root, True)
    if raw is None:
        return None
    try:
        behind, ahead = map(int, raw.split())
        return {"behind": behind, "ahead": ahead}
    except ValueError:
        return None


def status_counts(root):
    data = git(["status", "--porcelain=v1", "-z", "--untracked-files=normal", "--ignore-submodules=all"], root)
    parts = data.split(b"\0")
    tracked = untracked = 0
    i = 0
    while i < len(parts):
        part = parts[i]
        i += 1
        if not part:
            continue
        if part.startswith(b"??"):
            untracked += 1
        else:
            tracked += 1
            if len(part) >= 2 and (part[0:1] in (b"R", b"C")
                                   or part[1:2] in (b"R", b"C")):
                i += 1  # rename/copy includes an extra original path
    return {"tracked_changes": tracked, "untracked": untracked,
            "clean": tracked + untracked == 0}


def worktree_list(root):
    raw = text(["worktree", "list", "--porcelain"], root)
    entries = []
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        info = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            info[key] = value or True
        entries.append({
            "path": info.get("worktree"),
            "sha": info.get("HEAD"),
            "branch": str(info["branch"]).removeprefix("refs/heads/")
            if "branch" in info else None,
            "detached": "detached" in info, "locked": "locked" in info,
        })
    return entries


def community_files(root):
    checks = {
        "readme": ["README.md", "README.rst", "README"],
        "license": ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"],
        "contributing": ["CONTRIBUTING.md", ".github/CONTRIBUTING.md"],
        "code_of_conduct": ["CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md"],
        "security": ["SECURITY.md", ".github/SECURITY.md"],
        "support": ["SUPPORT.md", ".github/SUPPORT.md"],
        "accessibility": [".github/ACCESSIBILITY.md", "ACCESSIBILITY.md", "docs/ACCESSIBILITY.md"],
        "issue_templates": [".github/ISSUE_TEMPLATE"],
        "pr_template": [".github/pull_request_template.md", "PULL_REQUEST_TEMPLATE.md"],
    }
    return {name: any((root / p).exists() for p in paths)
            for name, paths in checks.items()}


def ecosystems(root):
    groups = {
        "node": ["package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"],
        "python": ["pyproject.toml", "uv.lock", "poetry.lock", "requirements.txt", "Pipfile.lock"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "go": ["go.mod", "go.sum", "go.work"],
        "java_kotlin": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle.kts"],
        "swift": ["Package.swift", "Package.resolved"],
        "dotnet": ["global.json", "Directory.Packages.props"],
        "ruby": ["Gemfile", "Gemfile.lock"],
        "php": ["composer.json", "composer.lock"],
        "infra": ["terraform.lock.hcl", ".terraform.lock.hcl", "Dockerfile"],
    }
    return {name: [p for p in paths if (root / p).is_file()]
            for name, paths in groups.items()
            if any((root / p).is_file() for p in paths)}


def npm_root_alignment(root):
    manifest = root / "package.json"
    lock = root / "package-lock.json"
    if not (manifest.is_file() and lock.is_file()):
        return {"applicable": False}
    try:
        package = json.loads(manifest.read_text(encoding="utf-8"))
        locked = json.loads(lock.read_text(encoding="utf-8"))
        if not isinstance(package, dict) or not isinstance(locked, dict):
            return {"applicable": True, "status": "unknown",
                    "reason": "Expected JSON objects for both npm files"}
        packages = locked.get("packages")
        if not isinstance(packages, dict):
            return {"applicable": True, "status": "unknown",
                    "reason": "Missing/invalid lockfile packages object"}
        root_deps = packages.get("")
        if root_deps is not None and not isinstance(root_deps, dict):
            return {"applicable": True, "status": "unknown",
                    "reason": "Invalid npm lock root package"}
        if root_deps is None:
            return {"applicable": True, "status": "unknown",
                    "reason": "lockfile lacks packages['']"}
        drift = []
        for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            expected, actual = package.get(field, {}), root_deps.get(field, {})
            if not isinstance(expected, dict) or not isinstance(actual, dict):
                return {"applicable": True, "status": "unknown",
                        "reason": "Invalid dependency map: " + field}
            for name in sorted(set(expected) | set(actual)):
                if expected.get(name) != actual.get(name):
                    drift.append({"category": field, "name": name})
        return {"applicable": True, "status": "aligned" if not drift else "drift",
                "lockfile_version": locked.get("lockfileVersion"),
                "drift": drift[:50], "additional_drift": max(0, len(drift) - 50)}
    except (OSError, ValueError, TypeError) as exc:
        return {"applicable": True, "status": "unknown", "reason": str(exc)[:200]}


def snapshot(base=None, max_branches=200):
    root = Path(text(["rev-parse", "--show-toplevel"])).resolve()
    head = text(["rev-parse", "HEAD"], root)
    branch = text(["symbolic-ref", "-q", "--short", "HEAD"], root, True)
    upstream = text(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], root, True)
    remote_head = text(["symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"], root, True)
    if base and not commit(base, root):
        raise RuntimeError("Explicit base ref not available locally: " + base)
    base_ref = base or remote_head
    base_sha = commit(base_ref, root) if base_ref else None
    trees = worktree_list(root)
    raw_refs = text(
        ["for-each-ref", "--sort=-committerdate",
         "--format=%(refname:short)%00%(objectname)%00%(upstream:short)%00%(upstream:track)",
         "refs/heads"], root
    )
    all_rows = [x for x in raw_refs.splitlines() if x]
    branches = []
    for line in all_rows[:max_branches]:
        name, sha, track, state = (line.split("\0") + [""] * 4)[:4]
        branches.append({
            "name": name, "sha": sha, "upstream": track or None,
            "tracking": state or None,
            "worktrees": [w["path"] for w in trees if w["branch"] == name],
            "base_divergence": divergence(base_sha, sha, root) if base_sha else None,
        })
    uncommitted_checks = {
        "working_diff_clean": git(["diff", "--no-ext-diff", "--no-textconv", "--check"], root, True) is not None,
        "staged_diff_clean": git(["diff", "--cached", "--no-ext-diff", "--no-textconv", "--check"], root, True) is not None,
    }
    return {
        "kind": "freview-local-readonly", "collected_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root), "head_sha": head, "branch": branch,
        "upstream": upstream, "remote_head_cached": remote_head,
        "base": {"ref": base_ref, "sha": base_sha, "divergence": divergence(base_sha, head, root)}
        if base_sha else None,
        "shallow": text(["rev-parse", "--is-shallow-repository"], root) == "true",
        "status": status_counts(root), "uncommitted_whitespace": uncommitted_checks,
        "worktrees": trees, "branches": branches,
        "branches_omitted": max(0, len(all_rows) - len(branches)),
        "community": community_files(root), "ecosystems_root_only": ecosystems(root),
        "npm_root_alignment": npm_root_alignment(root),
        "limitations": [
            "Remote-tracking refs may be stale: no fetch was performed.",
            "Only the current worktree's dirtiness is checked; other worktree contents are not read.",
            "No GitHub/GitLab issue, PR, security alert, CI, deployment or release evidence is collected.",
            "No source behavior, physical accessibility or deep code review was performed.",
            "Root-level ecosystem discovery is not exhaustive for monorepos.",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description="Read-only local freview metadata snapshot")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--base", default=None, help="exact locally available comparison ref")
    ap.add_argument("--max-branches", type=int, default=200, help="cap branch table length")
    a = ap.parse_args()
    if not 1 <= a.max_branches <= 2000:
        ap.error("--max-branches must be between 1 and 2000")
    try:
        result = snapshot(a.base, a.max_branches)
    except RuntimeError as exc:
        print(f"freview: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print("freview local (read-only) — " + result["collected_utc"])
        print("HEAD:", result["branch"] or "(detached)", result["head_sha"])
        print("Base:", result["base"] or "(not resolved locally)")
        print("Worktree status:", result["status"])
        print("Worktrees:", len(result["worktrees"]), "Branches:",
              len(result["branches"]), "omitted:", result["branches_omitted"])
        print("Community:", json.dumps(result["community"], sort_keys=True))
        print("Ecosystems:", json.dumps(result["ecosystems_root_only"], sort_keys=True))
        print("npm:", json.dumps(result["npm_root_alignment"], sort_keys=True))
        print("LIMIT: Git remote/CI freshness, functionality, release and physical QA are not verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
