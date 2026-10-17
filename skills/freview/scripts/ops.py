#!/usr/bin/env python3
"""freview ops: opt-in, shell-free, bounded local operations for trusted checkouts.

Read-only inventory is freview's default. This tool does NOT sandbox programs.
Executing project tests/agents requires separate explicit permission and scratch.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

MODULES = ("specs", "planning", "implementation", "tests", "adversarial",
           "mutation", "regression", "hooks", "shipping")
STAGES = ("implementation", "tests", "adversarial", "mutation", "regression")
LIMITS = {"timeout_seconds": 120, "max_rounds": 3, "max_output_bytes": 16384}
MAX_CONFIG = 65536
MAX_ARCHIVE = 32 * 1024 * 1024
MAX_UNPACKED = 64 * 1024 * 1024
MAX_MEMBERS = 4000
MAX_PROMPT = 4000
MARKER = "# FREVIEW-OPS-MANAGED:v1"
PROTECTED = ("main", "master", "develop", "release/*")
SHA = re.compile(r"^[0-9a-f]{40}$")
ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")


class OpsError(Exception):
    pass


def validate_policy(obj: object) -> dict:
    if not isinstance(obj, dict) or set(obj) - {"schema_version", "modules", "commands", "limits"}:
        raise OpsError("Invalid or unknown policy fields")
    if type(obj.get("schema_version")) is not int or obj["schema_version"] != 1:
        raise OpsError("Unsupported policy version")
    modules = {name: False for name in MODULES}
    selected = obj.get("modules", {})
    if not isinstance(selected, dict) or set(selected) - set(MODULES):
        raise OpsError("Unknown module")
    for name, value in selected.items():
        if type(value) is not bool:
            raise OpsError("Module flags must be booleans")
        modules[name] = value
    commands = obj.get("commands", {})
    if not isinstance(commands, dict) or set(commands) - set(STAGES):
        raise OpsError("Invalid command keys")
    clean_commands = {}
    for stage, argv in commands.items():
        if (not isinstance(argv, list) or not 1 <= len(argv) <= 32 or
                not all(isinstance(arg, str) and arg and len(arg) <= 2048
                        and "\0" not in arg and "\n" not in arg for arg in argv)):
            raise OpsError("Command must be a bounded argv array")
        lower = Path(argv[0]).name.lower()
        # This is a guardrail, not a general-purpose shell/code sandbox.
        if lower in {"sh", "bash", "zsh", "fish", "powershell", "pwsh",
                     "cmd", "npm", "npx", "pip", "pip3", "brew", "curl", "wget",
                     "sudo", "git"}:
            raise OpsError("Shell, installer, network and Git commands are not supported as stage launchers")
        if (len(argv) > 2 and Path(argv[0]).name.startswith("python")
                and argv[1:3] in (["-m", "pip"], ["-m", "ensurepip"])):
            raise OpsError("Package installation is prohibited")
        clean_commands[stage] = list(argv)
    raw_limits = obj.get("limits", {})
    if not isinstance(raw_limits, dict) or set(raw_limits) - set(LIMITS):
        raise OpsError("Unknown limits")
    limits = dict(LIMITS)
    limits.update(raw_limits)
    for key, (minimum, maximum) in {
        "timeout_seconds": (1, 600),
        "max_rounds": (1, 3),
        "max_output_bytes": (1024, 65536),
    }.items():
        value = limits[key]
        if type(value) is not int or not minimum <= value <= maximum:
            raise OpsError("Invalid limit: " + key)
    return {"schema_version": 1, "modules": modules,
            "commands": clean_commands, "limits": limits}


def load_policy(path: Path) -> dict:
    path = Path(path)
    if path.is_symlink():
        raise OpsError("Policy file must not be a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        with os.fdopen(os.open(path, flags), "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise OpsError("Policy must be a regular file")
            raw = source.read(MAX_CONFIG + 1)
        if len(raw) > MAX_CONFIG:
            raise OpsError("Policy too large")
        return validate_policy(json.loads(raw.decode("utf-8")))
    except (ValueError, UnicodeError, OSError) as exc:
        raise OpsError("Policy unreadable or invalid") from None


def status(policy: dict) -> dict:
    return {"schema_version": 1,
            "enabled": [key for key in MODULES if policy["modules"][key]],
            "disabled": [key for key in MODULES if not policy["modules"][key]],
            "limits": policy["limits"], "read_only_default": True,
            "execution_requires_explicit_flag": True, "release_automation": False}


def plan(policy: dict, requirements: str, sha: str) -> dict:
    if not policy["modules"]["planning"] or not policy["modules"]["specs"]:
        raise OpsError("Planning and specifications must both be enabled")
    if not isinstance(requirements, str) or not requirements.strip() or len(requirements) > MAX_PROMPT:
        raise OpsError("Requirements must be nonempty and bounded")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise OpsError("A full exact SHA is required")
    return {
        "schema_version": 1, "head_sha": sha,
        "requirements": requirements,
        "acceptance": ["Derive observable acceptance criteria from the approved requirements",
                       "Add failing tests before source edits", "Keep user and agent claims distinct from results"],
        "tasks": ["Freeze clean commit and branch policy", "Implement only approved scope",
                  "Run independently recorded tests and quality checks",
                  "Obtain adversarial review without worker summary first",
                  "Reconcile integration and prepare human shipping handoff"],
        "approval_required": True,
    }


def _git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    command = ["git", "-c", "core.fsmonitor=false",
               "-c", "core.hooksPath=/dev/null", *args]
    try:
        p = subprocess.run(command, cwd=repo, env=env, capture_output=True,
                           text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise OpsError("Git metadata unavailable") from None
    if p.returncode or len(p.stdout) > 65536:
        raise OpsError("Git metadata check failed or over budget")
    return p.stdout.strip()


def _repo_head(repo: Path) -> str:
    if not repo.is_dir() or repo.is_symlink():
        raise OpsError("Repository root missing or symlinked")
    top = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    if top != repo.resolve():
        raise OpsError("Target is not the repository root")
    sha = _git(repo, "rev-parse", "HEAD")
    if not SHA.fullmatch(sha):
        raise OpsError("Unborn or invalid HEAD")
    # Untracked files count; no dirty source can be represented by a single SHA.
    if _git(repo, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise OpsError("Dirty tree: no exact immutable snapshot including local changes")
    return sha


def _scratch(repo: Path, root: Path) -> Path:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise OpsError("Explicit existing scratch directory required")
    resolved = root.resolve()
    source = repo.resolve()
    if resolved == source or resolved in source.parents or source in resolved.parents:
        raise OpsError("Scratch must be outside checkout and its parent directories")
    if not os.access(resolved, os.W_OK | os.X_OK):
        raise OpsError("Scratch not writable")
    return resolved


def _extract_archive(repo: Path, root: Path, sha: str) -> Path:
    # Capture archive in explicit scratch, never tempfile's implicit internal root.
    working = Path(tempfile.mkdtemp(prefix="freview-ops-", dir=root))
    destination = working / "work"
    destination.mkdir()
    archive = working / "snapshot.tar"
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    try:
        with archive.open("wb") as sink:
            with subprocess.Popen(["git", "-c", "core.hooksPath=/dev/null",
                                   "-c", "core.fsmonitor=false", "archive",
                                   "--format=tar", sha], cwd=repo, env=env,
                                  stdout=sink, stderr=subprocess.DEVNULL) as proc:
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    raise OpsError("Git archive timed out")
                if proc.returncode:
                    raise OpsError("Git archive failed")
        if archive.stat().st_size > MAX_ARCHIVE:
            raise OpsError("Archive too large for configured safe bounds")
        with tarfile.open(archive, "r:") as tar:
            total = 0
            count = 0
            for member in tar:
                count += 1
                total += max(0, member.size)
                name = PurePosixPath(member.name)
                if (count > MAX_MEMBERS or total > MAX_UNPACKED or name.is_absolute()
                        or ".." in name.parts or
                        not (member.isfile() or member.isdir())):
                    raise OpsError("Unsupported or unsafe archive entry")
                target = destination.joinpath(*name.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as source, target.open("xb") as out:
                        shutil.copyfileobj(source, out)
                    target.chmod(0o700 if member.mode & 0o111 else 0o600)
        archive.unlink()
        return destination
    except Exception:
        # Constrained cleaning applies exclusively to our newly-created scratch,
        # never to the user's checkout or existing worktrees.
        shutil.rmtree(working, ignore_errors=True)
        raise


def _execute(stage: str, policy: dict, workspace: Path, storage: Path, sha: str,
             *, prompt: str = "") -> dict:
    if stage not in STAGES or not policy["modules"][stage]:
        raise OpsError("Stage disabled")
    argv = policy["commands"].get(stage)
    if not argv:
        raise OpsError("No explicit argv configured for enabled stage")
    if len(prompt) > MAX_PROMPT:
        raise OpsError("Review prompt over budget")
    if stage == "adversarial":
        # Never send worker's report or summary to the independent reviewer first.
        if "WORKER_SUMMARY" in prompt:
            raise OpsError("Reviewer cannot receive worker summary on first pass")
    limit = policy["limits"]["max_output_bytes"]
    logfile = storage / (stage + "-" + str(time.time_ns()) + ".log")
    start = time.monotonic()
    env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
           "FREVIEW_OPS_STAGE": stage, "FREVIEW_SOURCE_SHA": sha}
    # No implicit HOME, GitHub tokens or inherited API keys. This is not an OS
    # sandbox: an executable can still reach the host/network in many setups.
    try:
        with logfile.open("xb") as output:
            output.write(b"")   # artifact created by this tool in approved scratch
        process = subprocess.Popen(argv, cwd=workspace, env=env,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        try:
            stdout, _ = process.communicate(
                input=(prompt.encode("utf-8") if prompt else b""),
                timeout=policy["limits"]["timeout_seconds"])
            timed_out = False
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, _ = process.communicate()
            timed_out = True
        output_bytes = stdout[:limit]
        with logfile.open("wb") as output:
            output.write(output_bytes)
        status_text = "timeout" if timed_out else "passed" if process.returncode == 0 else "failed"
        return {"stage": stage, "status": status_text, "sha": sha,
                "exit_code": process.returncode, "elapsed_seconds": round(time.monotonic() - start, 3),
                "log_path": str(logfile), "output_truncated": len(stdout) > limit,
                "command_argv": argv, "proves_test_quality": False,
                "reviewer_independence_verified": False, "network_isolation": False}
    except OSError:
        raise OpsError("Configured executable unavailable or output unwritable") from None


def run_stage(stage: str, policy: dict, repo: Path, scratch: Path,
              *, allow_execute: bool = False, expected_sha: str | None = None,
              prompt: str = "") -> dict:
    if stage not in STAGES or not policy["modules"].get(stage):
        raise OpsError("Stage not enabled")
    if not allow_execute:
        raise OpsError("Execution requires --allow-execute and trusted checkout")
    repo = Path(repo)
    root = _scratch(repo, scratch)
    sha = _repo_head(repo)
    if expected_sha is not None and sha != expected_sha:
        raise OpsError("Expected exact SHA differs from HEAD")
    workspace = _extract_archive(repo, root, sha)
    return _execute(stage, policy, workspace, workspace.parent, sha, prompt=prompt)


def hook_allowed(kind: str, policy: dict, *, branch: str,
                 updates: list[str] | None = None) -> bool:
    if not policy["modules"]["hooks"] or kind not in ("pre-commit", "pre-push"):
        return False
    if any(_matches_branch(branch, protected) for protected in PROTECTED):
        return False
    if kind == "pre-push":
        for line in updates or []:
            parts = line.split()
            if len(parts) not in (2, 4):
                return False
            remote = parts[1] if len(parts) == 2 else parts[2]
            if not remote.startswith("refs/heads/"):
                return False
            target = remote[len("refs/heads/"):]
            if any(_matches_branch(target, protected) for protected in PROTECTED):
                return False
            if len(parts) == 4:
                old = parts[3]
                if old == "0" * 40:
                    continue
                # Cannot prove force-push safety from metadata alone.
                # Existing ref update requires explicit human verification.
                return False
    return True


def _matches_branch(value: str, pattern: str) -> bool:
    return value == pattern or (pattern.endswith("*") and value.startswith(pattern[:-1]))


def ship_plan(policy: dict, repo: Path, *, verified: bool) -> dict:
    if not policy["modules"]["shipping"] or not verified:
        raise OpsError("Shipping handoff requires enabled module and successful checks")
    sha = _repo_head(Path(repo))
    branch = _git(Path(repo), "symbolic-ref", "--quiet", "--short", "HEAD")
    if any(_matches_branch(branch, x) for x in PROTECTED):
        raise OpsError("Shipping from protected branch not permitted")
    return {"status": "handoff-only", "head_sha": sha, "branch": branch,
            "verified_reported": True, "pushed": False, "merged": False,
            "released": False, "deployment_performed": False,
            "required_human_gates": ["Review exact test/CI artifacts",
                                     "Review actual changes and security",
                                     "Authorize PR merge and release externally"]}


def install_hooks(policy: dict, repo: Path, *, allow_install: bool = False) -> list[str]:
    if not policy["modules"]["hooks"] or not allow_install:
        raise OpsError("Hooks require enabled module and explicit installation permission")
    repo = Path(repo).resolve()
    _repo_head(repo)
    configured = repo / ".freview-ops.json"
    if not configured.is_file() or configured.is_symlink():
        raise OpsError("Committed ops policy required for hooks")
    installed = load_policy(configured)
    if not installed["modules"]["hooks"]:
        raise OpsError("On-disk policy does not enable hooks")
    # Avoid silently bypassing an existing core.hooksPath policy.
    hook_path = subprocess.run(["git", "config", "--get", "core.hooksPath"],
                               cwd=repo, capture_output=True, text=True)
    if hook_path.returncode == 0 and hook_path.stdout.strip():
        raise OpsError("Existing core.hooksPath; refusing to replace")
    directory = Path(_git(repo, "rev-parse", "--git-path", "hooks"))
    if not directory.is_absolute():
        directory = repo / directory
    if directory.is_symlink() or not directory.is_dir():
        raise OpsError("Hooks destination unavailable")
    targets = [directory / "pre-commit", directory / "pre-push"]
    if any(target.exists() or target.is_symlink() for target in targets):
        raise OpsError("Existing hooks are never overwritten")
    command = (shlex.quote(sys.executable) + " " +
               shlex.quote(str(Path(__file__).resolve())) + " hook")
    bodies = [f"#!/bin/sh\n{MARKER}\nexec {command} {name} --repo {shlex.quote(str(repo))}\n"
              for name in ("pre-commit", "pre-push")]
    created = []
    try:
        for target, body in zip(targets, bodies):
            with target.open("x", encoding="utf-8") as handle:
                handle.write(body)
            target.chmod(0o700)
            created.append(str(target))
    except OSError:
        for name in created:
            Path(name).unlink(missing_ok=True)
        raise OpsError("Could not safely install hooks") from None
    return created


def uninstall_hooks(repo: Path) -> list[str]:
    repo = Path(repo).resolve()
    directory = Path(_git(repo, "rev-parse", "--git-path", "hooks"))
    if not directory.is_absolute():
        directory = repo / directory
    removed = []
    for name in ("pre-commit", "pre-push"):
        path = directory / name
        if path.is_symlink() or not path.is_file():
            continue
        if MARKER in path.read_text(encoding="utf-8", errors="replace")[:512]:
            path.unlink()
            removed.append(str(path))
    return removed


def pipeline(policy: dict, repo: Path, scratch: Path, *, allow_execute=False,
             expected_sha=None, requirements="", rounds=None) -> dict:
    if not allow_execute:
        raise OpsError("Pipeline requires explicit execution approval")
    repo = Path(repo)
    root = _scratch(repo, scratch)
    sha = _repo_head(repo)
    if expected_sha is not None and expected_sha != sha:
        raise OpsError("Pipeline SHA mismatch")
    rounds = policy["limits"]["max_rounds"] if rounds is None else rounds
    if type(rounds) is not int or rounds < 1 or rounds > 3 or rounds > policy["limits"]["max_rounds"]:
        raise OpsError("Invalid review round budget")
    if len(requirements) > MAX_PROMPT:
        raise OpsError("Requirements over budget")
    if policy["modules"]["implementation"] and not policy["modules"]["tests"]:
        raise OpsError("Autonomous implementation must have tests enabled")
    workspace = _extract_archive(repo, root, sha)
    storage = workspace.parent
    receipts = []
    verdict = "unverified"
    for cycle in range(1, rounds + 1):
        if policy["modules"]["implementation"]:
            report = _execute("implementation", policy, workspace, storage, sha,
                              prompt="Implement approved requirements with tests first:\n" + requirements)
            receipts.append(report)
            if report["status"] != "passed":
                verdict = "worker-failed"
                break
        if policy["modules"]["tests"]:
            report = _execute("tests", policy, workspace, storage, sha)
            receipts.append(report)
            if report["status"] != "passed":
                verdict = "tests-failed"
                break
        if policy["modules"]["adversarial"]:
            report = _execute("adversarial", policy, workspace, storage, sha,
                prompt="Independent audit: inspect requirements, source, tests and skipped cases. "
                       "Do not read worker summary. Inspect test quality and evidence.\n" + requirements)
            receipts.append(report)
            if report["status"] != "passed":
                verdict = "review-process-failed"
                continue
        verdict = "checks-executed-without-authenticated-verdict"
        break
    if verdict == "checks-executed-without-authenticated-verdict":
        for name in ("regression", "mutation"):
            if policy["modules"][name]:
                result = _execute(name, policy, workspace, storage, sha)
                receipts.append(result)
                if result["status"] != "passed":
                    verdict = name + "-failed"
                    break
    return {"source_sha": sha, "review_cycles": cycle, "verdict": verdict,
            "executions": receipts, "scratch_workspace": str(workspace),
            "independent_success_authenticated": False,
            "automatic_push_or_release": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "plan", "run", "pipeline",
                    "ship", "hook", "install-hooks", "uninstall-hooks"))
    parser.add_argument("stage", nargs="?", help="run stage or hook name")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--requirements", default="")
    parser.add_argument("--allow-execute", action="store_true")
    parser.add_argument("--allow-install", action="store_true")
    parser.add_argument("--verified", action="store_true")
    parser.add_argument("--rounds", type=int)
    args = parser.parse_args()
    try:
        repo = args.repo.absolute()
        policy = load_policy(args.policy if args.policy else repo / ".freview-ops.json") if (
            args.policy or (repo / ".freview-ops.json").exists()
        ) else validate_policy({"schema_version": 1})
        if args.action == "status":
            result = status(policy)
        elif args.action == "plan":
            result = plan(policy, args.requirements, args.expected_sha or _repo_head(repo))
        elif args.action == "run":
            if not args.scratch:
                raise OpsError("Explicit --scratch required")
            result = run_stage(args.stage or "", policy, repo, args.scratch,
                               allow_execute=args.allow_execute, expected_sha=args.expected_sha,
                               prompt=args.requirements)
        elif args.action == "pipeline":
            if not args.scratch:
                raise OpsError("Explicit --scratch required")
            result = pipeline(policy, repo, args.scratch,
                              allow_execute=args.allow_execute, expected_sha=args.expected_sha,
                              requirements=args.requirements, rounds=args.rounds)
        elif args.action == "ship":
            result = ship_plan(policy, repo, verified=args.verified)
        elif args.action == "install-hooks":
            result = {"installed": install_hooks(policy, repo, allow_install=args.allow_install)}
        elif args.action == "uninstall-hooks":
            if not args.allow_install:
                raise OpsError("Uninstall requires explicit --allow-install")
            result = {"uninstalled": uninstall_hooks(repo)}
        elif args.action == "hook":
            branch = _git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
            updates = sys.stdin.read(8192).splitlines() if args.stage == "pre-push" else []
            permitted = hook_allowed(args.stage or "", policy, branch=branch, updates=updates)
            result = {"allowed": permitted, "kind": args.stage, "branch": branch}
            print(json.dumps(result))
            return 0 if permitted else 2
        else:
            raise OpsError("Unknown action")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except OpsError as exc:
        # No contents/paths from project scripts or logs echoed.
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
