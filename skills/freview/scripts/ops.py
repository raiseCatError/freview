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
import selectors
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
FORWARDABLE_ENV = {"HOME", "XDG_CONFIG_HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR",
                   "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"}
SHA = re.compile(r"^[0-9a-f]{40}$")
ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")


class OpsError(Exception):
    pass


def validate_policy(obj: object) -> dict:
    if not isinstance(obj, dict) or set(obj) - {"schema_version", "modules", "commands", "limits", "pass_env"}:
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
    forward = obj.get("pass_env", [])
    if (not isinstance(forward, list) or len(forward) != len(set(map(str, forward)))
            or not all(isinstance(name, str) and name in FORWARDABLE_ENV for name in forward)):
        raise OpsError("Invalid environment forwarding request")
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
            "commands": clean_commands, "limits": limits, "pass_env": forward}


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
            "execution_requires_explicit_flag": True, "release_automation": False,
            "credentials_require_separate_flag": bool(policy.get("pass_env"))}


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
             *, prompt: str = "", allow_credentials: bool = False) -> dict:
    if stage not in STAGES or not policy["modules"][stage]:
        raise OpsError("Stage disabled")
    argv = policy["commands"].get(stage)
    if not argv:
        raise OpsError("No explicit argv configured for enabled stage")
    if len(prompt) > MAX_PROMPT:
        raise OpsError("Prompt exceeds budget")
    if stage == "adversarial" and "WORKER_SUMMARY" in prompt:
        raise OpsError("Reviewer cannot receive worker summary on first pass")
    cap = policy["limits"]["max_output_bytes"]
    logfile = storage / (stage + "-" + str(time.time_ns()) + ".log")
    begin = time.monotonic()
    deadline = begin + policy["limits"]["timeout_seconds"]
    env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
           "FREVIEW_OPS_STAGE": stage, "FREVIEW_SOURCE_SHA": sha}
    if policy.get("pass_env") and not allow_credentials:
        raise OpsError("Credential forwarding requires --allow-credentials")
    if allow_credentials:
        env.update({key: os.environ[key] for key in policy.get("pass_env", [])
                    if key in os.environ})
    process = None
    captured = 0
    truncated = False
    timed_out = False
    try:
        # Selector-driven capped streaming: communicate() would hold unbounded
        # output in memory before slicing, allowing denial-of-service.
        with logfile.open("xb") as output:
            process = subprocess.Popen(argv, cwd=workspace, env=env,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        timed_out = True
                        break
                    ready = selector.select(timeout=remaining)
                    if not ready:
                        timed_out = True
                        break
                    for key, _ in ready:
                        chunk = os.read(key.fd, min(8192, cap - captured + 1))
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        kept = chunk[:max(0, cap - captured)]
                        output.write(kept)
                        captured += len(kept)
                        if len(chunk) > len(kept):
                            truncated = True
                            break
                    if truncated:
                        break
            if timed_out or truncated:
                process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        state = ("timeout" if timed_out else "output-limit" if truncated else
                 "passed" if process.returncode == 0 else "failed")
        return {"stage": stage, "status": state, "sha": sha,
                "exit_code": process.returncode,
                "elapsed_seconds": round(time.monotonic() - begin, 3),
                "log_path": str(logfile), "output_truncated": truncated,
                "command_argv": argv, "proves_test_quality": False,
                "reviewer_independence_verified": False, "network_isolation": False}
    except (OSError, BrokenPipeError, ValueError):
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        raise OpsError("Configured executable unavailable or output unwritable") from None


def run_stage(stage: str, policy: dict, repo: Path, scratch: Path,
              *, allow_execute: bool = False, allow_credentials: bool = False,
              expected_sha: str | None = None, prompt: str = "") -> dict:
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
    return _execute(stage, policy, workspace, workspace.parent, sha,
                    prompt=prompt, allow_credentials=allow_credentials)



def regression_sensitivity(policy: dict, repo: Path, scratch: Path,
                           *, base_sha: str, test_paths: list[str],
                           allow_execute: bool = False,
                           allow_credentials: bool = False,
                           expected_sha: str | None = None) -> dict:
    """Run candidate tests on both candidate and baseline in separate scratch trees.

    Baseline failure is an observation, not proof that the test is meaningful:
    dependency/configuration drift can also produce a failing baseline.
    """
    if not allow_execute or not policy["modules"]["regression"] or not policy["modules"]["tests"]:
        raise OpsError("Regression sensitivity requires enabled tests/regression and explicit approval")
    if "tests" not in policy["commands"]:
        raise OpsError("Configured test command missing")
    if not isinstance(base_sha, str) or not SHA.fullmatch(base_sha):
        raise OpsError("Exact baseline SHA required")
    if not isinstance(test_paths, list) or not 1 <= len(test_paths) <= 24:
        raise OpsError("Explicit bounded changed test paths required")
    repo = Path(repo)
    root = _scratch(repo, scratch)
    head = _repo_head(repo)
    if expected_sha is not None and expected_sha != head:
        raise OpsError("Candidate SHA mismatch")
    if head == base_sha:
        raise OpsError("Baseline and candidate cannot be identical")
    for value in test_paths:
        if (not isinstance(value, str) or len(value) > 400 or
                PurePosixPath(value).is_absolute() or
                any(part in ("", ".", "..", ".git") for part in PurePosixPath(value).parts) or
                len(PurePosixPath(value).parts) < 2):
            raise OpsError("Unsafe test path")
    # Neither user checkout nor another worktree is modified; only fresh
    # disposable copies in the caller's explicitly selected scratch directory.
    candidate = _extract_archive(repo, root, head)
    baseline = _extract_archive(repo, root, base_sha)
    for value in test_paths:
        source = candidate.joinpath(*PurePosixPath(value).parts)
        target = baseline.joinpath(*PurePosixPath(value).parts)
        if (source.is_symlink() or not source.is_file() or
                source.stat().st_size > 1_048_576 or
                any(part.is_symlink() for part in source.parents if part != candidate)):
            raise OpsError("Changed test path unavailable, symlinked or oversized")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise OpsError("Unsafe baseline test target")
        shutil.copyfile(source, target)
    current = _execute("tests", policy, candidate, candidate.parent, head,
                       allow_credentials=allow_credentials)
    if current["status"] != "passed":
        return {"status": "candidate-failed", "candidate": current, "baseline": None,
                "proves_test_quality": False, "explanation": "Candidate tests did not pass"}
    old = _execute("tests", policy, baseline, baseline.parent, base_sha,
                   allow_credentials=allow_credentials)
    state = ("baseline-failure-observed" if old["status"] == "failed"
             else "no-sensitivity-observed" if old["status"] == "passed"
             else "inconclusive")
    return {"status": state, "candidate": current, "baseline": old,
            "test_paths": test_paths, "proves_test_quality": False,
            "explanation": ("A baseline failure might be a meaningful regression test "
                            "or unrelated incompatibility; inspect assertion results")}

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
    protected_source = any(_matches_branch(branch, x) for x in PROTECTED)
    return {"status": "handoff-only", "head_sha": sha, "branch": branch,
            "verified_reported": True, "pushed": False, "merged": False,
            "released": False, "deployment_performed": False,
            "protected_source_branch": protected_source,
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
    common = Path(_git(repo, "rev-parse", "--git-common-dir"))
    directory = (common if common.is_absolute() else repo / common) / "hooks"
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
    common = Path(_git(repo, "rev-parse", "--git-common-dir"))
    directory = (common if common.is_absolute() else repo / common) / "hooks"
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
             allow_credentials=False, expected_sha=None, requirements="", rounds=None) -> dict:
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
    generated_plan = plan(policy, requirements, sha) if (policy["modules"]["planning"]
                  and policy["modules"]["specs"]) else None
    workspace = _extract_archive(repo, root, sha)
    storage = workspace.parent
    receipts = []
    verdict = "unverified"
    for cycle in range(1, rounds + 1):
        if policy["modules"]["implementation"]:
            report = _execute("implementation", policy, workspace, storage, sha,
                              prompt="Implement approved requirements with tests first:\n" + requirements,
                              allow_credentials=allow_credentials)
            receipts.append(report)
            if report["status"] != "passed":
                verdict = "worker-failed"
                break
        if policy["modules"]["tests"]:
            report = _execute("tests", policy, workspace, storage, sha,
                              allow_credentials=allow_credentials)
            receipts.append(report)
            if report["status"] != "passed":
                verdict = "tests-failed"
                break
        if policy["modules"]["adversarial"]:
            report = _execute("adversarial", policy, workspace, storage, sha,
                prompt="Independent audit: inspect requirements, source, tests and skipped cases. "
                       "Do not read worker summary. Inspect test quality and evidence.\n" + requirements,
                allow_credentials=allow_credentials)
            receipts.append(report)
            if report["status"] != "passed":
                verdict = "review-process-failed"
                continue
        verdict = "checks-executed-without-authenticated-verdict"
        break
    if verdict == "checks-executed-without-authenticated-verdict":
        for name in ("regression", "mutation"):
            if policy["modules"][name]:
                result = _execute(name, policy, workspace, storage, sha,
                                  allow_credentials=allow_credentials)
                receipts.append(result)
                if result["status"] != "passed":
                    verdict = name + "-failed"
                    break
    shipping = (ship_plan(policy, repo, verified=True)
                if policy["modules"]["shipping"] and
                   verdict == "checks-executed-without-authenticated-verdict" else None)
    return {"source_sha": sha, "review_cycles": cycle, "verdict": verdict,
            "plan": generated_plan, "shipping": shipping,
            "executions": receipts, "scratch_workspace": str(workspace),
            "independent_success_authenticated": False,
            "automatic_push_or_release": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "plan", "run", "pipeline", "sensitivity",
                    "ship", "hook", "install-hooks", "uninstall-hooks"))
    parser.add_argument("stage", nargs="?", help="run stage or hook name")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--requirements", default="")
    parser.add_argument("--allow-execute", action="store_true")
    parser.add_argument("--allow-credentials", action="store_true")
    parser.add_argument("--allow-install", action="store_true")
    parser.add_argument("--verified", action="store_true")
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--base-sha")
    parser.add_argument("--test-path", action="append", default=[])
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
                               allow_execute=args.allow_execute, allow_credentials=args.allow_credentials,
                               expected_sha=args.expected_sha,
                               prompt=args.requirements)
        elif args.action == "pipeline":
            if not args.scratch:
                raise OpsError("Explicit --scratch required")
            result = pipeline(policy, repo, args.scratch,
                              allow_execute=args.allow_execute,
                              allow_credentials=args.allow_credentials,
                              expected_sha=args.expected_sha,
                              requirements=args.requirements, rounds=args.rounds)
        elif args.action == "sensitivity":
            if not args.scratch:
                raise OpsError("Explicit --scratch required")
            result = regression_sensitivity(policy, repo, args.scratch,
                  base_sha=args.base_sha, test_paths=args.test_path,
                  allow_execute=args.allow_execute,
                  allow_credentials=args.allow_credentials,
                  expected_sha=args.expected_sha)
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
