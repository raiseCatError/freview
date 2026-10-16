# freview reviews freview

*The repository auditor has turned its clipboard on itself. Recursion depth: one. Ego protection: disabled.*

**freview = Full Review**, pronounced **“f-review”** (the letter F, then “review”), **not** “free-view” or “fre-view.”

| | |
| --- | --- |
| Audit timestamp | **2026-10-16 20:35 UTC** |
| Target repository | [raiseCatError/freview](https://github.com/raiseCatError/freview) |
| Baseline | `main` at [`1560b0a1`](https://github.com/raiseCatError/freview/commit/1560b0a18b9291f1c56cbb47c3e473ec2294f9fa) |
| Requested scope | **Full-mode** delivery, hygiene, source-code quality, Git, security posture, docs and duplicate tracking |
| Verification classification | **partial-audit**: source-level Full-mode review performed, but unavailable local installations and agent integrations could not be independently verified |
| Machine-readable report | [JSON findings, evidence manifest and remediation plan](freview-reviews-freview.json) |
| Changes proposed | Accompanying PR: targeted correctness, security, report and documentation fixes; no automatic cleanup |

> **Verdict:** Ready to try as a read-only **preview on trusted repositories**, but not yet a fully validated unattended review product. The jokes are optional; the evidence requirements aren't.

## 1. What actually shipped, and what did not

| Area | Source and observed outcome | Status |
| --- | --- | --- |
| Core skill | [Agent Skill](../skills/freview/SKILL.md) with discovery-first modes, references, and specialist preferences | Implemented on `main` |
| Local tools | `repo_snapshot.py`, `review.py`, `report_tools.py`, `duplicates.py` | Implemented; limited to local structural/review-metadata tasks |
| Standard mode | Git/issue/CI/hygiene metadata; no implementation or deep source-code review by default | Documented, fixture-tested |
| Full mode | Agent-directed source/feature tracing and code review plus standard metadata | Instructions exist; installed-agent end-to-end acceptance **pending** |
| Git and worktrees | Main SHA and GitHub branches accessible; no local user's worktree or unpushed edits accessible | **Partial** coverage |
| GitHub delivery | Four merged PRs [#1](https://github.com/raiseCatError/freview/pull/1), [#2](https://github.com/raiseCatError/freview/pull/2), [#3](https://github.com/raiseCatError/freview/pull/3), [#4](https://github.com/raiseCatError/freview/pull/4); no standalone issues at audit baseline | Metadata observed |
| CI | [GitHub Actions run 38961320971](https://github.com/raiseCatError/freview/actions/runs/38961320971) succeeded on macOS and Ubuntu at the audited exact SHA | Automated fixture checks passed |
| Release | No published freview GitHub Release or v0.1.0 tag returned | **Not released** |
| Community | README, MIT license, contributing, conduct, support, security and accessibility guidance | Good coverage; GitHub description and contribution templates can improve |
| Dependencies | No third-party Python runtime dependencies in helpers; no root dependency lockfile needed for the standard-library-only project | GitHub Dependency graph may be empty by design |
| Duplicate work | Four PRs cover distinct design, security, hardening and dogfooding phases; no duplicate issue/PR pair **confirmed** from examined metadata | None confirmed; not an exhaustive guarantee |

**History is not a cleanup instruction.** Five branch heads existed at this review stage, including historical feature, hardening and documentation branches. Freview should never suggest deleting one without verifying release ancestry, ownership and active worktrees first.

## 2. Findings from the source-level review

I reviewed the four Python helpers, their test fixtures, the bundled/public JSON schemas, the official-first specialist catalog, the skill instructions, the CI definitions and the daily workflow template. These are **source inspection and existing CI evidence**, not a claim that a full local clone or official external code reviewer was run.

| ID | Priority | Finding | Actual disposition |
| --- | --- | --- | --- |
| **FR-01** | P1 | Optional daily workflow pointed at a different helper path than the distributed skill | **Corrected in accompanying PR**, needs consumer-workflow smoke test |
| **FR-02** | P1 | npm manifest/lockfile paths could follow external symlinks or cause oversized reads | **Guarded in accompanying PR**, regression cases added |
| **FR-03** | P1 | Duplicate candidate list could grow quadratically for repeated matching titles | **Output bounded in accompanying PR**; worst-case comparisons still quadratic |
| **FR-04** | P2 | Two JSON reports with no repository identity could compare as if from the same repo | **Corrected in accompanying PR** |
| **FR-05** | P2 | Project-config JSON schema and Python validator disagreed on bounds | **Aligned in accompanying PR** |
| **FR-06** | P1 | Real installed Claude Code, Codex, OpenCode, Antigravity CLI (agy) orchestration is still unverified | **Outstanding acceptance gate** |
| **FR-07** | P2 | GitHub description and issue/PR contribution templates not present | Optional community improvement |
| **FR-08** | P2 | Historical merged branch heads remain in GitHub branch list | **Not a defect by itself**; explicitly preserve |

### The two most important issues

**FR-06: Full is not the same as verified.** `freview full` tells the *agent* to collect hosted GitHub facts, inspect feature wiring and perform code review. Its local Python helper intentionally emits a `local-snapshot`, never a `full-audit`. The reporter validates structure and required evidence manifests, but a plausible URL isn't independent proof that a reviewer actually opened it. A real four-agent acceptance matrix remains important.

**FR-02: read-only should mean no unexpected file reads.** The previous parser used `Path.is_file` and `read_text` on the root npm files without rejecting symlinks or checking size first. The proposed tests use files outside the fixture root and an oversized lockfile. The new behavior reports `unknown` instead of reading out-of-root data or calling the dependency state clean.

### Duplicate checking did **not** review code clones

Freview's duplicate checker looks for **issues, PRs, roadmap items and overlapping delivery requests**, not repeated functions, copied implementations or code clones. Similar titles only create **candidates**, and a PR that closes an issue is not a duplicate of that issue. This run confirmed no duplicated work items in the scoped GitHub issue/PR inventory, not that there could be none in inaccessible projects or worktrees.

## 3. Proposed how-to-fix plan (not executed by the audit)

| Priority | Action | Verification gate |
| --- | --- | --- |
| P1 | **Merge the reviewed helper/template corrections** only after exact-PR-head CI passes | macOS + Ubuntu suite and new edge-case fixtures |
| P1 | **Smoke-test actual agent installations** (Claude, Codex, OpenCode, agy) on a disposable repo; invoke Standard and Full; verify references and official review permissions | Capture tool version, command, exact SHA, evidence manifest and permissions |
| P1 | **Test the opt-in daily workflow in a consumer fixture** with an explicitly installed, pinned skill | Clear missing-skill failure, UTC schedule, no default artifact upload |
| P2 | **Scale duplicate search only when needed** | Profile real inputs; candidate-only results, bounded output, no code-clone claims |
| P2 | **Improve repository description/templates if contributions warrant it** | Confirm better newcomer workflow and no noise |
| P2 | **Inspect old branch ancestry only with worktree visibility and maintainer approval** | No automatic pruning/deletion |

Each recommendation is scoped to the smallest meaningful change, with verification separated from implementation. Detailed machine-readable remediation steps and their evidence appear in [the JSON report](freview-reviews-freview.json). No feature-implementation brainstorming was requested, and this audit did not invent new product features to build.

## 4. Security and trust-boundary review

**Existing strengths:** Freview's Git wrapper strips inherited `GIT_*` variables, disables known filesystem-monitor hooks, external diffs and configured clean/process/smudge drivers, uses noninteractive subprocesses, and does not fetch or prune. Config is declarative; project policy cannot silently elevate Standard to Full or enable external vulnerability scans. Saved JSON reports require explicit output and are created owner-only. The opt-in GitHub Actions template uses pinned official Actions and disables artifact upload by default.

**Remaining boundaries:** This is not a sandbox. A hostile Git binary, Git implementation flaw, race involving replaced files, or malicious permissions environment isn't neutralized merely by avoiding hooks. The tool should run against genuinely untrusted repositories in an isolated environment, with no developer credentials. The report **did not run** an external vulnerability scanner or penetration test.

**Specialists:** Official Claude Code Review and OpenAI Codex review remain recommended only when genuinely installed/available and authorized. No plugin/paid service was invoked or billed during this review. A Full-mode source inspection performed here does **not** mean an official reviewer executed.

## 5. Explicit gaps: why this is `partial-audit`

- The container could not resolve GitHub for `git clone`; source and history were inspected using the connected GitHub API, not an executable local checkout. The helper itself and the fixture suite were **not** rerun from the audit host.
- The audit could not observe the maintainer's unpushed branches, active Mac worktrees, installed skill discovery, private security alert settings or branch-protection policy.
- There was no real user-interface/accessibility physical test, no external security scan, and no permission to trigger paid code-review services.
- The code changes accompanying this report require **new exact-head CI**. Prior green main CI is evidence only for the already-audited baseline.

The accompanying JSON report sets `report_kind=partial-audit`, includes a per-category `verification_manifest`, lists eight findings and eight non-executed repair proposals, and names the checks that could not be observed. This is a **Full-mode review performed to the available evidence boundary**, not a false certificate of complete verification.

---

## 6. The recursive conclusion

**freview can review freview, but freview must not approve freview merely because freview says freview looks fine.**

No confirmed duplicate tickets. No mysteriously “shipped” release. Real code fixes identified. Security limits remain explicit. A green check proves the checked commit passed the checked tests — not that the auditor has transcended the need for independent verification.

*Full Review. Pronounced **f-review**. Not “fre-view.” Recursion depth: 1.*
