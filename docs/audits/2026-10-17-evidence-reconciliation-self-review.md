# freview evidence reconciliation — bounded self-review and handoff

**Date:** 2026-10-17 UTC
**Branch:** `feature/evidence-reconciliation-20261017`
**PR:** https://github.com/raiseCatError/freview/pull/16
**Classification:** **bounded hosted source audit**, not a native agent Full audit, independently reproduced test run or security certification.
**Base:** `2646e4c35e2383b108a752893d846cd48989f2a8` on `main`.
**Source inspected:** PR #16 diff and current source of both new helpers, regression fixtures, report changes, README, SKILL and reference protocol.
**No direct edits to `main`, no tags/releases, no automatic merge.**

## Product scope

**Audit the repo, not the summary.** Maintain evidence reconciliation as a read-only overlay across Spec Kit/OpenSpec requirements, implementation claims, local Git/worktree state, exact-SHA verification, integration and publishing. Do not compete with gstack's lifecycle workflows, Nonna's enforcement, OpenSpec/Spec Kit's spec creation, or official code reviewers. No third-party source copied; all code in this PR is project-authored and standard-library-only.

## Review: C1 specification inventory

- Discovers candidate OpenSpec/Spec Kit paths and returns metadata only. Reports truncation and missing artifacts explicitly. It does not read spec bodies or run discovered tooling.
- Caught and fixed a breadth-budget issue: the first implementation counted only matching files and could traverse arbitrarily many irrelevant entries. Now all visited directory entries count toward the global bound and `os.scandir` is consumed without materializing a huge directory listing.
- Caught and fixed an intermediate-symlink issue: a symlink at `openspec/` could previously redirect inspection even if `openspec/specs/` itself wasn't a symlink. Parent components are checked and dedicated regression coverage was added.
- **Remaining:** concurrent hostile filesystem mutation may race the path-based checks; this helper is **not an OS sandbox**. A generic `specs/` directory can be labeled a Spec Kit *candidate* despite no Spec Kit installation. Input root/path metadata may be private; don't publish without review. Large/hostile checkouts need filesystem isolation.

## Review: C2 verification receipts

- Requires complete lowercase 40-character SHAs, bounded command/evidence metadata and reported exit codes; tracks mismatches, invalid fields, missing artifacts, reported failures and unauthenticated independent-actor assertions without executing tests.
- Caught and fixed a status precedence issue: contradictory SHA errors were formerly swallowed by a generic invalid status.
- Caught and fixed a malformed-actor crash (list/object instead of string) and inconsistent `provenance_verified` on the non-object failure path.
- Caught and fixed receipt schema version accepting `true` or `1.0` via Python equality; optional note/suite fields now have bounded types.
- Reading uses a bounded, no-follow regular-file descriptor where supported. A final review found a potential FIFO-open hang; the helper now opens nonblocking and rejects non-regular input before any read, with a dedicated regression. Input and output contain **untrusted assertions**. No JSON receipt can prove execution, test adequacy, or reviewer independence.
- **Remaining:** named URLs are not fetched/authenticated, log/JUnit contents aren't independently inspected, commands aren't replayed, and live CI provenance isn't proven by this helper. The separate agent Full audit must do that with authorization.

## Review: C3 report integration

- Optional `spec_sources` and `claim_evidence` are in both identical schema copies. Old v1 reports remain valid. Agent-provided evidence includes source actor, requirement/test/integration/publication refs and orthogonal lifecycle, evidence, test-quality states.
- Comparator now surfaces added/changed/disappeared claim evidence only when both reports include these fields. It explicitly avoids calling disappeared evidence a resolved problem. Duplicate claim IDs and impossible worker-only independent reproduction claims are rejected as structurally inconsistent.
- The independent verification playbook requires the auditor to examine original requirements and code before the worker's summary; any reruns, baseline tests, mutation or worktree creation are **separately authorized** and resource-bounded.
- **Remaining:** a valid report schema does not verify that a reported independent audit took place; an AI-authored state can still be wrong.

## Review: C4 adversarial fixture coverage

- `tests/fixtures/evidence_scenarios.json` labels 11 scenarios with explicit expected statuses, covering stale SHAs, red tests, missing logs, declared independence, rewritten tests and ambiguous or absent specs.
- The fixture tests intentionally preserve two known blind spots as *known misses*: green rewritten/weakened tests, and generic `specs/` directory false candidates.
- Existing Git fixture tests already cover local-only commits, worktrees and tracking-cache limitations; no duplicate synthetic scenarios were added simply to inflate numbers.
- **Remaining:** no independent second model has reviewed the branch, no live worker-vs-auditor benchmark was run, and the fixtures don't measure production defect-detection accuracy.

## Automated evidence and limits

- C1 exact head `438d99b7`: https://github.com/raiseCatError/freview/actions/runs/38986224178 — Ubuntu/macOS successful.
- C2 hardened head `92a9aa2c`: https://github.com/raiseCatError/freview/actions/runs/38986782933 — Ubuntu/macOS successful.
- C3 exact head `50b203c6`: https://github.com/raiseCatError/freview/actions/runs/38987190435 — Ubuntu/macOS successful.
- C4 fixture head `b83890c1`: https://github.com/raiseCatError/freview/actions/runs/38987377142 — Ubuntu/macOS successful.
- C4 subsequent hardening head `f83f272a`: https://github.com/raiseCatError/freview/actions/runs/38987468323 — Ubuntu/macOS successful.
- **Final head (including later receipt regression tests and this review): requires its own exact-head workflow result; check PR #16 Actions and the actual branch SHA rather than relying on these older runs.** The source review itself was done with hosted GitHub reading, not local code execution on the owner's workstation.

## Outstanding human and external gates

- Native skill activation and Full agent delivery across actual Claude Code, Codex, OpenCode, Antigravity versions is **not re-executed in this cycle**; earlier maintainer confirmations remain historical evidence, not fresh independent QA.
- Mutation checks, full-suite reruns in real user codebases, Spec Kit convergence, OpenSpec verify, hosted compare benchmarks, filesystem-race/credential-isolation adversarial audit, security scanning and accessibility field QA remain unperformed.
- Does not install software, run mutation frameworks, configure required merge checks, or enforce production release gates.
- No evidence that a paid hosted market exists or adoption has been validated; external-user benchmark is a future decision gate.
- **Release hold:** leave PR #16 draft, do not merge, tag, publish, auto-schedule or delete historical worktrees/branches.

## Reviewer disposition

**Changes fit the targeted niche and expose their limitations without requiring new runtime dependencies.** No new P0/P1 code defect was confirmed during this bounded review after the fixes above. That is *not* proof no defects remain. The proper next handoff is (1) confirm final exact-head CI, (2) review PR diff + safety boundaries, (3) optional real multi-agent user acceptance and ground-truth benchmark, and (4) separate owner authorization for merge/release.
