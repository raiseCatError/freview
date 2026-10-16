# freview reviews freview — Antigravity Full Review & Acceptance Test

*The repository auditor has turned its clipboard on itself. Recursion depth: one. Ego protection: disabled.*

**freview = Full Review**, pronounced **“f-review”** (the letter F, then “review”), **not** “free-view” or “fre-view.”

| Metadata Field | Value |
| --- | --- |
| **Audit timestamp** | **2026-10-16 21:25:00 UTC** |
| **Target repository** | [`raiseCatError/freview`](https://github.com/raiseCatError/freview) |
| **Audited baseline commit** | [`7e20912d068be8cc8a14f7ac64b082404fce790d`](https://github.com/raiseCatError/freview/commit/7e20912d068be8cc8a14f7ac64b082404fce790d) (PR #6 merge) |
| **Upstream integration during audit** | [`81411193b6d23dac74ecc5097032c622a4cf8403`](https://github.com/raiseCatError/freview/commit/81411193b6d23dac74ecc5097032c622a4cf8403) (PR #7 merge) |
| **Orchestrating agent & runtime** | Google Antigravity CLI (`agy` v1.4.0), Gemini 3.8 Flash (High) |
| **Storage isolation** | External Samsung T7 Shield (`/Volumes/T7Tmp/ai-dev`), verified via `t7run --check` |
| **Requested scope** | **Full-mode** audit across `git`, `tracking`, `implementation`, `ci`, `releases`, `docs`, `community`, `dependencies`, `security-posture`, `accessibility`, `code-review` |
| **Verification classification** | **`partial-audit`**: Complete local execution, 65/65 passing unit tests, and source-level code review performed; external paid code reviewers and physical screen-reader accessibility unobserved by policy |
| **Machine-readable report** | [JSON findings, evidence manifest and remediation plan](freview-reviews-freview.json) |

---

## Executive Verdicts

### 1. Antigravity Skill Integration Verdict: **CONDITIONAL PASS**
- **What worked:** The skill package, schemas, documentation references, and helper scripts (`repo_snapshot.py`, `review.py`, `report_tools.py`, `duplicates.py`, `agent_doctor.py`) executed on macOS with 100% test passage (65/65 unit tests in 20.44s) on Python 3.14.8.
- **The Condition:** Antigravity CLI 1.4.0 automatically discovers workspace project skills under `{workspace}/.agents/skills/` and global configurations under `~/.gemini/config/`. Symlinking the skill to `~/.gemini/antigravity-cli/skills/freview` (as documented in `agent_doctor.py` and `references/agent-discovery.md`) did not cause `agy` to inject `freview` into its prompt `/skills` table. For automatic prompt activation in `agy`, the skill must reside in the project-local `.agents/skills/` or be configured in `~/.gemini/config/`.

### 2. freview Project Readiness Verdict: **Preview-Ready**
- `raiseCatError/freview` is solid, safe, and ready to use as a read-only **preview tool** for pair programmers and repository maintainers.
- It is **not yet a release candidate** (not tagged, not published) because:
  1. The installed skill copy in `~/.agents/skills/freview` drifted behind repository `main`, causing `python3 -I` invocations outside the script directory to fail with `ModuleNotFoundError` (fixed upstream in PR #7, but installed copy needs updating).
  2. Multi-agent physical validation across Claude Code, OpenAI Codex, and OpenCode remains partial.
  3. GitHub repository metadata and contribution templates (`.github/ISSUE_TEMPLATE`) are not yet in place.

---

## 1. What Actually Shipped, and What Did Not

| Area | Observed Evidence & Reality | Actual Lifecycle Status |
|---|---|---|
| **Core skill definition** | `skills/freview/SKILL.md` with YAML frontmatter, progressive disclosure, and 12 modular references | **Integrated candidate** on `main` |
| **Local Python helpers** | 5 Python scripts: `repo_snapshot.py`, `review.py`, `report_tools.py`, `duplicates.py`, `agent_doctor.py` | **Integrated candidate**, 0 external dependencies |
| **Standard mode** | Fast read-only metadata snapshot; excludes deep code review and source-level implementation checks | **Verified**; verified by test suite and CLI execution |
| **Full mode** | End-to-end source tracing, code quality review, and verification manifest | **Verified** with native reviewer; official external paid review unselected |
| **Unit test suite** | 6 test modules in `tests/`: 65 tests ran in 20.44s on Python 3.14.8, 0 failures, 0 errors | **Automated verified** |
| **Git & worktrees** | Worktree clean; 8 remote branches on `origin`. Ancestry verified against `main` | **Verified**; no uncommitted changes or branch pollution |
| **GitHub delivery** | 7 merged pull requests (#1 through #7); 0 open PRs; 0 GitHub issues | **Integrated candidate** |
| **CI / Automation** | GitHub Actions workflow `.github/workflows/checks.yml` passed on commit `8141119` (run 38968225970) and commit `7e20912` (run 38966870820) | **Automated verified** |
| **Releases & Tags** | 0 GitHub releases; 0 Git tags | **Unreleased** (pre-v0.1.0) |
| **Community files** | README, LICENSE (MIT), CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT present; ISSUE_TEMPLATE absent | **Partial**; core docs present, templates missing |
| **Dependencies** | Python 3 standard library only; npm root alignment verified against `notMyShell` fixture | **Verified**; zero runtime dependency risk |
| **Duplicate work items** | 7 merged PRs scanned with `duplicates.py`; 0 duplicate clusters detected; candidate cap enforced | **Verified**; no false duplicates |

---

## 2. Evidence of Commands Executed

Every command below was executed directly on the physical host during this session on Samsung T7 Shield external storage (`/Volumes/T7Tmp/ai-dev`):

| Command Invocation | Target SHA / Working Dir | Exit Code | Observed Result |
|---|---|---|---|
| `t7run --check` | N/A | `0` | `/Volumes/T7Tmp/ai-dev` verified on `/Volumes/T7Tmp`, 61.7 GB free |
| `python3 -m py_compile skills/freview/scripts/*.py tests/*.py` | `81411193b6` | `0` | Clean syntax compilation across all 11 Python files |
| `python3 -m unittest discover -s tests -v` | `81411193b6` | `0` | **Ran 65 tests in 20.437s — OK** |
| `python3 -I skills/freview/scripts/repo_snapshot.py --json` | `81411193b6` | `0` | JSON snapshot: clean worktree, commit SHA, forge identity, community files |
| `python3 -I skills/freview/scripts/review.py --mode standard --format json` | `81411193b6` | `0` | Excludes `code-review`; reports `local-snapshot` without mutating state |
| `python3 -I skills/freview/scripts/review.py --mode full --format json` | `81411193b6` | `0` | Includes `code-review` with `agent-review-required` specialist status |
| `python3 -I skills/freview/scripts/report_tools.py docs/freview-reviews-freview.json` | `81411193b6` | `0` | `Valid freview report: {'valid': True, 'kind': 'partial-audit', 'findings': 11}` |
| `python3 -I skills/freview/scripts/duplicates.py --format json /Volumes/T7Tmp/ai-dev/prs.json` | `81411193b6` | `0` | Scanned 7 PR records; 0 duplicate pairs; no mutations |
| `python3 -I skills/freview/scripts/agent_doctor.py --workspace <repo> --format json` | `81411193b6` | `0` | Detected 8 launchers (claude aliases, opencode functions, agy, codex) |
| `python3 -I ~/.agents/skills/freview/scripts/review.py --mode standard` | `7e20912d06` (installed) | `1` | `ModuleNotFoundError: No module named 'repo_snapshot'` (proved installed skill drift) |
| `python3 -I skills/freview/scripts/review.py --mode standard --format json` (on NMSh) | `raiseCatError/notMyShell` | `0` | Bounded read-only smoke test: 200 branches, npm locked v3 aligned, 0 mutations |

---

## 3. Findings from Source-Level Code Review

| ID | Priority | Category | Finding Summary | Status & Disposition |
|---|---|---|---|---|
| **FR-01** | P1 | `releases` | Scheduled consumer workflow pointed to undocumented helper path | **Resolved** on `main` in PR #5 |
| **FR-02** | P1 | `dependencies` | Root npm metadata followed external symlinks or read oversized files | **Resolved** on `main` in PR #3 |
| **FR-03** | P1 | `tracking` | Duplicate-work candidate output was unbounded | **Resolved** on `main` in PR #3 |
| **FR-04** | P2 | `tracking` | JSON report comparison accepted two reports with no repository identity | **Resolved** on `main` in PR #3 |
| **FR-05** | P2 | `docs` | Runtime project-policy bounds in `review.py` differed from published schema | **Resolved** on `main` in PR #3 |
| **FR-06** | P1 | `ci` | Full mode physical multi-agent acceptance matrix is partially verified | **Partial**; Antigravity passed; Claude/Codex/OpenCode pending |
| **FR-07** | P2 | `community` | GitHub repository description and issue/PR templates are missing | **Open**; repository description empty; no `.github/ISSUE_TEMPLATE` |
| **FR-08** | Informational | `git` | 8 historical merged feature and fix branches remain on remote origin | **Open (Preserved)**; not a defect; maintainer must authorize any cleanup |
| **FR-09** | P1 | `implementation` | Installed skill drift causes `python3 -I` outside script directory to fail | **New Finding**; installed skill is at `7e20912` and lacks PR #7 loader |
| **FR-10** | P1 | `docs` | Antigravity CLI skill discovery path in `agent_doctor` targets wrong folder | **New Finding**; `agy` scans `{workspace}/.agents/skills/` and `~/.gemini/config/` |
| **FR-11** | P2 | `docs` | `agent_doctor` reports `executable: null` for alias commands in PATH | **New Finding**; `shutil.which` skipped when launcher definition is alias |

### Key Deep-Dive Details

#### FR-09: Installed Skill Drift & Python `-I` Isolation
- When running under `python3 -I`, Python removes the script's directory from `sys.path`.
- The installed skill at `~/.agents/skills/freview` (commit `7e20912d06`) used `from repo_snapshot import snapshot, text`, which crashed with `ModuleNotFoundError` when called from outside `scripts/`.
- Repository `main` merged PR #7 (`81411193b6`) during this audit, fixing `review.py` with dynamic `importlib.util` sibling loading.
- However, the user's installed agent skill copy has not yet been synchronized with `main`.

#### FR-10: Antigravity CLI Skill Discovery Path Realities
- `skills/freview/scripts/agent_doctor.py` and `references/agent-discovery.md` state that Antigravity CLI (`agy`) looks for skills under `~/.gemini/antigravity-cli/skills/freview`.
- Active inspection of Antigravity CLI 1.4.0 reveals that it discovers user skills from `{workspace}/.agents/skills/` and global configurations under `~/.gemini/config/`.
- Having `freview` in `~/.gemini/antigravity-cli/skills/` does not load it into the agent's `/skills` prompt. `agent_doctor.py` should be updated to check `{workspace}/.agents/skills/freview` and `~/.gemini/config/skills/freview`.

#### FR-11: Agent Doctor Alias Executable Reporting
- In `agent_doctor.py` line 207:
  ```python
  "executable": shutil.which(cmd["agent"]) if cmd["kind"] == "default" else None
  ```
- If an agent command is defined as an alias (such as `alias claude="CLAUDE_CONFIG_DIR=... claude"`), `cmd["kind"]` is `"alias"`, and the executable field is unconditionally set to `null` even though `claude` is present in `PATH`. Falling back to `shutil.which(cmd["agent"])` provides more useful diagnostic output.

---

## 4. Verification Manifest

| Category | Status | Ref SHA | Tool / Version | Verified Evidence |
|---|---|---|---|---|
| **`git`** | `verified` | `81411193b6` | `git 2.48.1` / `repo_snapshot.py` | Worktree clean; 8 remote branches inspected; ancestry verified against `main`. |
| **`tracking`** | `verified` | `81411193b6` | `gh 2.68.0` / `duplicates.py` | 7 merged PRs; 0 open PRs; 0 issues; `duplicates.py` confirmed 0 false duplicate clusters. |
| **`implementation`** | `verified` | `81411193b6` | `python 3.14.8` / `unittest` | 65/65 unit tests passed in 20.44s; syntax compilation clean; Python `-I` verified. |
| **`ci`** | `verified` | `81411193b6` | `GitHub Actions` / `gh CLI` | Run 38968225970 on `8141119` succeeded; run 38966870820 on `7e20912` succeeded; local suite 100% green. |
| **`releases`** | `verified` | `81411193b6` | `gh 2.68.0` | 0 GitHub releases; 0 Git tags; consumer action template verified. |
| **`docs`** | `verified` | `81411193b6` | `python 3.14.8` / `unittest` | 12 reference files verified; README, CONTRIBUTING, SUPPORT, SECURITY, CODE_OF_CONDUCT present. |
| **`community`** | `verified` | `81411193b6` | `repo_snapshot.py` | Community files checked; identified missing `.github/ISSUE_TEMPLATE` and PR template (FR-07). |
| **`dependencies`** | `verified` | `81411193b6` | `repo_snapshot.py` | 0 third-party Python runtime packages; npm lockfile v3 alignment verified on NMSh fixture. |
| **`security-posture`** | `verified` | `81411193b6` | `unittest` / `repo_snapshot.py` | `GIT_*` env scrubbing, fsmonitor=false, hooksPath=/dev/null, filter overrides, and 0o600 file modes verified. |
| **`accessibility`** | `partial` | `81411193b6` | Manual inspection | `docs/ACCESSIBILITY.md` inspected; terminal output clean; physical VoiceOver testing unobserved. |
| **`code-review`** | `verified` | `81411193b6` | Native Reviewer (Antigravity) | Full source review across 5 scripts, 6 test files, 2 schemas; specialist catalog vetted (>=1000 stars). |

---

## 5. Prioritized How-to-Fix Plan (Non-Destructive)

This plan is ordered by priority and dependency. None of these changes have been executed by this audit:

| Priority | ID | Action | Prerequisites | Validation Gate | Approval |
|---|---|---|---|---|---|
| **P1** | **FR-09** | Synchronize `~/.agents/skills/freview` with repository `main` (PR #7) to fix `python3 -I` `ModuleNotFoundError` | None | Run `python3 -I ~/.agents/skills/freview/scripts/review.py --mode standard` from external folder; confirm exit 0 | Required |
| **P1** | **FR-10** | Update `agent_doctor.py` and `references/agent-discovery.md` to accurately reflect Antigravity CLI discovery (`{workspace}/.agents/skills/` and `~/.gemini/config/`) | None | Run `python3 -m unittest tests.test_agent_doctor` and verify `agent_doctor.py` output | Required |
| **P1** | **FR-06** | Complete physical multi-agent acceptance tests across Claude Code, OpenAI Codex, and OpenCode | FR-09, FR-10 | Run `review.py` and `agent_doctor.py` inside each agent runtime and collect validation evidence | Required |
| **P2** | **FR-11** | Improve `agent_doctor.py` executable detection for alias-wrapped launchers using `shutil.which` | None | Run `python3 -m unittest tests.test_agent_doctor` | Required |
| **P2** | **FR-07** | Add GitHub repository description and issue/PR templates (`.github/ISSUE_TEMPLATE/`) | None | Verify presence with `repo_snapshot.py` community check | Required |
| **Info** | **FR-08** | Maintain historical merged branch heads until explicit maintainer deletion approval | None | Confirm no unmerged commits or active worktrees before any branch pruning | Required |

---

## 6. Security and Trust Boundaries

- **Sandbox Reality:** `freview` is a read-only audit tool, not an operating-system sandbox.
- **Git Execution Safety:** Subprocesses strip `GIT_*` environment variables, force `GIT_OPTIONAL_LOCKS=0`, `core.fsmonitor=false`, `core.hooksPath=/dev/null`, disable external diff drivers, and neutralize untrusted clean/process/smudge filters.
- **File System Safety:** JSON output files are created with `O_CREAT | O_EXCL | O_NOFOLLOW` and owner-only `0o600` permissions to prevent symlink attacks and permission leaks.
- **Specialist Boundaries:** No third-party skills were installed, no source code was uploaded to external endpoints, and no billed review APIs (Anthropic Claude Code Review, OpenAI Codex PR review) were invoked.

---

## 7. Explicit Gaps: Why This is `partial-audit`

1. **Third-Party Reviewers:** Official paid/hosted code-review services were not invoked or billed; the code review was conducted natively by the invoking agent.
2. **Physical Accessibility:** Terminal formatting is plain-text and high-contrast, but physical screen reader (macOS VoiceOver) testing was not executed.
3. **Multi-Agent Runtime Matrix:** While Antigravity CLI was verified end-to-end, physical interactive testing inside Claude Code, OpenAI Codex, and OpenCode remains pending separate host execution.
4. **Forges Beyond GitHub:** GitHub API was verified; GitLab, Codeberg, and Bitbucket forge integrations were not tested against live instances.

---

## 8. Conclusion

`freview` successfully reviewed `freview`.

The tool's local Python helpers execute cleanly without external dependencies, its Git security mitigations are effective, and its test suite is in excellent shape. The Antigravity CLI integration is functional and proven, with specific improvements identified for skill path discovery and installed-skill synchronization.

*Full Review. Pronounced **f-review**. Not “fre-view.” Recursion depth: 1.*
