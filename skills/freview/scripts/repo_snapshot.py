#!/usr/bin/env python3
"""freview local snapshot: read-only Git and filesystem metadata, Python stdlib only.

Does not fetch, install, execute project code, alter branches or delete files.
This complements (does not replace) the agent's forge/CI and implementation review.
"""
import argparse
import errno
import datetime as dt
import json
import os
import re
from urllib.parse import urlsplit
from pathlib import Path
import subprocess
import sys
import stat
import selectors
import time



MAX_GIT_OUTPUT = 4 * 1024 * 1024
MAX_GIT_STDERR = 64 * 1024


def _bounded_command(command, cwd, env, timeout, stdout_limit=MAX_GIT_OUTPUT,
                     stderr_limit=MAX_GIT_STDERR):
    """Read both pipes concurrently with fixed budgets; kill on overrun."""
    with subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        selector = selectors.DefaultSelector()
        selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
        selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
        data = {"stdout": bytearray(), "stderr": bytearray()}
        limits = {"stdout": stdout_limit, "stderr": stderr_limit}
        deadline = time.monotonic() + timeout
        try:
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("Git subprocess timed out")
                ready = selector.select(remaining)
                if not ready:
                    raise RuntimeError("Git subprocess timed out")
                for key, _ in ready:
                    channel = key.data
                    allowed = limits[channel] - len(data[channel])
                    chunk = os.read(key.fileobj.fileno(), min(65536, allowed + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif len(chunk) > allowed:
                        raise RuntimeError("Git subprocess " + channel + " exceeded byte budget")
                    else:
                        data[channel].extend(chunk)
            proc.wait(timeout=max(0, deadline - time.monotonic()))
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
            raise
        finally:
            selector.close()
        return subprocess.CompletedProcess(command, proc.returncode,
                                           bytes(data["stdout"]), bytes(data["stderr"]))


def _disabled_filter_settings(cwd, env):
    """Neutralize configured Git clean/process/smudge hooks from untrusted repo."""
    probe_command = ["git", "config", "--includes", "--null", "--name-only",
                     "--get-regexp", r"^filter\..*\.(clean|process|smudge)$"]
    try:
        probe = _bounded_command(probe_command, cwd, env, 10, stdout_limit=65536)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Could not inspect Git filter settings safely") from exc
    if probe.returncode == 1:
        return []
    if probe.returncode or len(probe.stdout) > 65536:
        raise RuntimeError("Git filter inspection failed; refusing audit")
    try:
        keys = [x.decode("utf-8", "strict") for x in probe.stdout.split(b"\0") if x]
    except UnicodeDecodeError as exc:
        raise RuntimeError("Invalid Git filter configuration; refusing audit") from exc
    if len(keys) > 256:
        raise RuntimeError("Too many Git filter drivers; refusing audit")
    overrides = []
    for key in sorted(set(keys)):
        if not key.startswith("filter.") or not key.endswith((".clean", ".process", ".smudge")):
            raise RuntimeError("Unexpected Git filter name; refusing audit")
        overrides.extend(["-c", key + "="])
    return overrides


def git(args, cwd=None, allowed_failure=False):
    # Git's inherited environment can override repository discovery/config
    # and activate trace-file writes. Reconstruct a safe Git-specific env rather
    # than allowing caller-provided GIT_CONFIG_*, GIT_TRACE*, GIT_INDEX_FILE,
    # GIT_EXTERNAL_DIFF or other unexpected GIT_* settings through.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_")}
    # Git's fsmonitor setting can execute arbitrary local programs even for
    # 'git status'. Force off at invocation time; do not trust repository config.
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_ATTR_NOSYSTEM"] = "1"
    try:
        filter_overrides = _disabled_filter_settings(cwd, env)
        p = _bounded_command(
            ["git", "--no-optional-locks",
             "-c", "core.fsmonitor=false",
             "-c", "core.hooksPath=" + os.devnull,
             "-c", "diff.external=",
             "-c", "core.pager=cat",
             *filter_overrides, *args], cwd, env, 20
        )
    except RuntimeError:
        # Limit violations must always abort; allowed_failure applies only to
        # ordinary Git nonzero results, never safety-budget failures.
        raise
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
    return text(["rev-parse", "--verify", "--quiet", "--end-of-options", ref + "^{commit}"], root, True)


def divergence(base, head, root):
    raw = text(["rev-list", "--left-right", "--count", base + "..." + head], root, True)
    if raw is None:
        return None
    try:
        behind, ahead = map(int, raw.split())
        return {"behind": behind, "ahead": ahead}
    except ValueError:
        return None


def safe_origin_identity(root):
    """Normalize common forge remotes without recording tokens or userinfo.

    Unknown/private-domain remotes are deliberately not exported.
    Worktrees with no comparable public remote share a common-dir identity.
    """
    raw = text(["config", "--local", "--get", "remote.origin.url"], root, True)
    recognized = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org"}
    if raw and len(raw) <= 2048:
        remote = raw.strip()
        # Reject potentially ambiguous URLs including credential/query tokens.
        if any(ch in remote for ch in ("?", "#", "\n", "\r")):
            remote = ""
        host = path = None
        # URL syntax must be parsed before SSH scp syntax: otherwise
        # 'https://host/org/repo' is misread as host='https'.
        if "://" in remote:
            try:
                parsed = urlsplit(remote)
                if (parsed.scheme in ("https", "http", "ssh", "git") and
                        not parsed.username and not parsed.password and
                        parsed.port is None):
                    host = (parsed.hostname or "").lower()
                    path = parsed.path.lstrip("/")
            except ValueError:
                pass
        else:
            ssh = re.fullmatch(r"(?:[^@/:]+@)?([A-Za-z0-9.-]+):([^:]+)", remote)
            if ssh:
                host, path = ssh.group(1).lower(), ssh.group(2)
        if host in recognized and path:
            path = path.rstrip("/")
            if path.endswith(".git"):
                path = path[:-4]
            segments = path.split("/")
            # A verified conventional namespace/repository URL, not arbitrary input.
            if 2 <= len(segments) <= 6 and all(
                re.fullmatch(r"[A-Za-z0-9_.-]+", v) and v not in (".", "..")
                for v in segments
            ):
                return {"identity": "forge:" + host + "/" +
                        (path.lower() if host == "github.com" else path),
                        "public_remote": "https://" + host + "/" + path}
    common = text(["rev-parse", "--git-common-dir"], root, True)
    if not common:
        return {"identity": None, "public_remote": None}
    location = Path(common)
    if not location.is_absolute():
        location = root / location
    return {"identity": "gitdir:" + str(location.resolve()),
            "public_remote": None}


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


def local_change_inventory(root, max_paths=40):
    """Enumerate the current checkout; never reads the contents of changed files.

    Porcelain -z avoids quoting ambiguities. This captures staged, unstaged
    and untracked paths separately, including local work not committed anywhere.
    Paths are private metadata and must not be published without review.
    """
    raw = git(["status", "--porcelain=v1", "-z", "--untracked-files=normal",
               "--ignore-submodules=all"], root)
    staged, unstaged, untracked = [], [], []
    fields = raw.split(b"\0")
    i = 0
    while i < len(fields):
        item = fields[i]
        i += 1
        if not item:
            continue
        status = item[:2]
        path = item[3:].decode("utf-8", "backslashreplace")
        if status == b"??":
            untracked.append(path)
        else:
            if status[:1] not in (b" ", b"?"):
                staged.append(path)
            if status[1:] not in (b" ", b"?"):
                unstaged.append(path)
            if b"R" in status or b"C" in status:
                i += 1  # Git's rename/copy record has a second NUL-terminated path.
    def bucket(paths):
        return {"count": len(paths), "sample_paths": paths[:max_paths],
                "omitted": max(0, len(paths) - max_paths)}
    return {"staged": bucket(staged), "unstaged": bucket(unstaged),
            "untracked": bucket(untracked),
            "note": "Only path/status inventory, not a code review or a diff-content audit. "
                    "Ignored files and other worktrees are not included. Treat local paths as private."}


def cached_tracking_state(root, head_sha):
    """Never assert 'pushed' based solely on possibly stale remote-tracking refs."""
    remote = text(["remote"], root, True)
    upstream = text(["rev-parse", "--abbrev-ref", "--symbolic-full-name",
                     "@{upstream}"], root, True)
    upstream_sha = commit(upstream, root) if upstream and head_sha else None
    counts = divergence(upstream_sha, head_sha, root) if upstream_sha else None
    if head_sha is None:
        state = "unborn-no-local-commits"
    elif not upstream:
        state = "no-configured-upstream"
    elif counts is None:
        state = "tracking-comparison-unavailable"
    elif counts["ahead"]:
        state = "local-commits-ahead-of-cached-upstream"
    elif counts["behind"]:
        state = "behind-cached-upstream"
    else:
        state = "matches-cached-upstream"
    return {"state": state, "upstream": upstream, "cached_upstream_sha": upstream_sha,
            "ahead": counts["ahead"] if counts else None,
            "behind": counts["behind"] if counts else None,
            "remotes_configured": bool(remote),
            "remote_publishing_verified": False,
            "note": "Cached refs cannot prove whether commits have been pushed to any remote. "
                    "Verify remotely for publication, CI and release claims."}


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
    if not (manifest.exists() or manifest.is_symlink()) or not (lock.exists() or lock.is_symlink()):
        return {"applicable": False}
    try:
        def bounded_json(path, limit):
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                         getattr(os, "O_NONBLOCK", 0))
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("npm metadata is not a regular file")
                if info.st_size > limit:
                    raise ValueError("npm metadata exceeds bounded read size")
                raw = stream.read(limit + 1)
            if len(raw) > limit:
                raise ValueError("npm metadata exceeds bounded read size")
            return json.loads(raw.decode("utf-8"))

        package = bounded_json(manifest, 2 * 1024 * 1024)
        locked = bounded_json(lock, 16 * 1024 * 1024)
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
    except OSError as exc:
        # OS exception strings can contain absolute private local paths.
        reason = ("Symlinked npm manifests were not read" if exc.errno == errno.ELOOP
                  else "Unable to read npm metadata safely")
        return {"applicable": True, "status": "unknown", "reason": reason}
    except (ValueError, TypeError) as exc:
        reason = ("npm metadata exceeds bounded read size"
                  if str(exc) == "npm metadata exceeds bounded read size"
                  else "Invalid npm metadata")
        return {"applicable": True, "status": "unknown", "reason": reason}


def snapshot(base=None, max_branches=200, categories=None,
             max_divergences=40, scan_worktrees=False, max_worktrees=12):
    # The standalone snapshot inspects all local structural categories; the
    # config-aware helper passes explicit selected categories and must not read
    # dependency/community files when the user excluded them.
    selected = set(categories) if categories is not None else None
    check_deps = selected is None or "dependencies" in selected
    check_community = selected is None or bool(
        selected & {"community", "docs", "accessibility"})
    root = Path(text(["rev-parse", "--show-toplevel"])).resolve()
    head = text(["rev-parse", "HEAD"], root, True)
    branch = text(["symbolic-ref", "-q", "--short", "HEAD"], root, True)
    upstream = text(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], root, True)
    remote_head = text(["symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"], root, True)
    if base and not commit(base, root):
        raise RuntimeError("Explicit base ref not available locally: " + base)
    base_ref = base or remote_head
    base_sha = commit(base_ref, root) if base_ref else None
    trees = worktree_list(root)
    repo_identity = safe_origin_identity(root)
    raw_refs = text(
        ["for-each-ref", "--sort=-committerdate",
         "--format=%(refname:short)%00%(objectname)%00%(upstream:short)%00%(upstream:track)",
         "refs/heads"], root
    )
    all_rows = [x for x in raw_refs.splitlines() if x]
    branches = []
    divergence_cache = {}
    divergence_calls = 0
    divergence_skipped = 0
    for line in all_rows[:max_branches]:
        name, sha, track, state = (line.split("\0") + [""] * 4)[:4]
        compared = None
        if base_sha:
            if sha in divergence_cache:
                compared = divergence_cache[sha]
            elif divergence_calls < max_divergences:
                compared = divergence(base_sha, sha, root)
                divergence_cache[sha] = compared
                divergence_calls += 1
            else:
                divergence_skipped += 1
        branches.append({
            "name": name, "sha": sha, "upstream": track or None,
            "tracking": state or None,
            "worktrees": [w["path"] for w in trees if w["branch"] == name],
            "base_divergence": compared,
            "divergence_checked": bool(base_sha and sha in divergence_cache),
        })
    uncommitted_checks = {
        "working_diff_clean": git(["diff", "--no-ext-diff", "--no-textconv", "--check"], root, True) is not None,
        "staged_diff_clean": git(["diff", "--cached", "--no-ext-diff", "--no-textconv", "--check"], root, True) is not None,
    }
    other_worktree_checks = []
    if scan_worktrees:
        for entry in trees:
            if entry.get("path") == str(root):
                continue
            if len(other_worktree_checks) >= max_worktrees:
                break
            other_root = entry.get("path")
            try:
                other_worktree_checks.append({
                    "path": other_root, "branch": entry.get("branch"),
                    "sha": entry.get("sha"),
                    "status": status_counts(Path(other_root)),
                })
            except (RuntimeError, OSError) as exc:
                other_worktree_checks.append({
                    "path": other_root, "status": "not-observed",
                    "reason": str(exc)[:160],
                })
    return {
        "kind": "freview-local-readonly", "collected_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root), "head_sha": head, "branch": branch,
        "repo_identity": repo_identity["identity"], "public_remote": repo_identity["public_remote"],
        "upstream": upstream, "remote_head_cached": remote_head,
        "base": {"ref": base_ref, "sha": base_sha, "divergence": divergence(base_sha, head, root)}
        if base_sha else None,
        "shallow": text(["rev-parse", "--is-shallow-repository"], root) == "true",
        "status": status_counts(root), "uncommitted_whitespace": uncommitted_checks,
        "local_changes": local_change_inventory(root),
        "publishing": cached_tracking_state(root, head),
        "worktrees": trees, "worktree_status_checks": other_worktree_checks,
        "other_worktrees_scanned": bool(scan_worktrees),
        "worktrees_not_scanned": max(0, len(trees) - 1 -
                                      len(other_worktree_checks)) if scan_worktrees else
                                 max(0, len(trees) - 1),
        "branches": branches,
        "branch_divergence_budget": max_divergences,
        "unique_branch_divergences_checked": divergence_calls,
        "branch_divergences_skipped_due_budget": divergence_skipped,
        "branches_omitted": max(0, len(all_rows) - len(branches)),
        "branches_omitted_is_lower_bound": False,
        "community": community_files(root) if check_community else {},
        "ecosystems_root_only": ecosystems(root) if check_deps else {},
        "npm_root_alignment": (npm_root_alignment(root) if check_deps
                               else {"applicable": False, "not_checked": True}),
        "limitations": [
            "Remote-tracking refs may be stale: no fetch was performed.",
            "Other worktrees are not inspected by default; --scan-worktrees is bounded and opt-in.",
            "Staged/unstaged/untracked paths are inventoried, but their contents and ignored files are not audited.",
            "Remote-tracking refs cannot establish whether local commits have been pushed.",
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
    ap.add_argument("--max-divergences", type=int, default=40,
                    help="max unique branch-vs-base divergence calculations, default 40")
    ap.add_argument("--scan-worktrees", action="store_true",
                    help="opt-in read-only status of other worktrees (metadata only)")
    ap.add_argument("--max-worktrees", type=int, default=12,
                    help="max other worktree status checks, default 12")
    a = ap.parse_args()
    if not 1 <= a.max_branches <= 2000:
        ap.error("--max-branches must be between 1 and 2000")
    if not 0 <= a.max_divergences <= 2000:
        ap.error("--max-divergences must be between 0 and 2000")
    if not 1 <= a.max_worktrees <= 40:
        ap.error("--max-worktrees must be between 1 and 40")
    try:
        result = snapshot(a.base, a.max_branches,
                          max_divergences=a.max_divergences,
                          scan_worktrees=a.scan_worktrees,
                          max_worktrees=a.max_worktrees)
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
