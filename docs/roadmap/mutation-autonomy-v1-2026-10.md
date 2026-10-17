# freview Mutation & Bounded Autonomy v1 — tests-first specification

**Date:** 2026-10-17. **Status:** implementation, review and initial final-head CI complete; owner merge/release held. 
**Branch:** `feature/mutation-autonomy-v1-20261017`, stacked onto draft PR #19 at `e2b269ea6f56b0caed1ac898584476bef5ec4f6f`. Neither this branch nor ancestors may merge/release without separate approval.

## Product intent and borrowed practices

**Audit the repo, not the summary.** The default freview skill and all optional operations stay **OFF/read-only**. Improve what happens *after* a maintainer explicitly opts into mutation and bounded worker/reviewer operations. Implement first-party, dependency-free **report interpretation and budget enforcement**, not a clone of mutation engines or general purpose agent OS.

- [StrykerJS](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/): consume mutation-testing-elements JSON (status Killed/Timeout/Survived/NoCoverage/CompileError/RuntimeError/Ignored/Pending). Recognize only Killed+Timeout as detected; Survived+NoCoverage as undetected. Ignore invalid/ignored in denominator and *never score incomplete/pending as green*. Prefer scoped runs and incremental/force where supported; caveat that incremental results can go stale with dependency/environment changes.
- [mutmut](https://mutmut.readthedocs.io/en/latest/): consume `mutants/mutmut-cicd-stats.json` produced by *explicitly configured* `mutmut export-cicd-stats`. Recognize `killed`, `survived`, `no_tests`, `timeout`, `skipped`, `suspicious`, `segfault`, `check_was_interrupted_by_user`. A missing file or interrupted run cannot pass.
- [OpenHands iteration budgets](https://docs.openhands.dev/openhands/usage/run-openhands/github-action): bounded stage/round budgets matter; use a global stage cap, stop if worker repeats findings with no file change.
- gstack, Nonna, GSD, Spec Kit: retain explicit acceptance plan, automated tests before review, review with genuine source observation, and a human-controlled release handoff. No third-party source vendored.

## Configuration / defaults

All modules remain OFF absent an explicit `.freview-ops.json`. Existing `limits` remain compatible. New optional `mutation_quality`:
- `format`: `auto` (default), `stryker`, `mutmut`.
- `mode`: `advisory` (default) or `gate`. A requested mutation run **cannot count as passing** from process exit alone even in advisory mode: missing/malformed/incomplete report yields explicit `mutation-inconclusive`. In gate mode, valid report must meet configured score and sample.
- `min_score`: 60% (advisory reporting default; gate threshold if enabled); `min_valid_mutants`: 1; `max_survivors`: 12 shown per report.
- Report discovery: only fixed known relative paths under the per-stage verifier workspace; no symlink/hardlink escape, no internet fetch, no reporter installation. Mutator invoked only when policy+command+allow-execute; no self-install or implicit reruns.
- A report without any valid mutants, with incomplete/pending observations, or a nonzero command exit is NOT green. Never claim score is correctness proof; report errors and representative survivors.
New optional `autonomy`:
- `max_stage_runs`: 12 (hard cap 32; applies across all nested worker/test/reviewer/mutation/regression calls).
- `stop_on_no_progress`: true. If reviewer requests change, next worker produces no candidate source change, stop with `no-progress` rather than burning next review tokens.
- `max_repeated_findings`: 1 (1–3) stops identical repeated finding fingerprints, even if the worker makes unrelated changes; prevents review oscillation.
- `require_mutation_for_shipping`: false by default. If opted in, no shipping handoff without a successful mutation gate on same candidate. Shipping remains handoff-only, never merge/deploy.
- Existing max 3 review rounds, explicit scratch, exact SHA, credential flags and no automatic original-repo edits remain.
- No automatic local worktree resets, installs, pip/npm, branch pushes or external PR/releases. No OS sandbox promises.

## Checkpoints

### M0 — red tests first
- [x] Create branch from exact PR #19 head, write durable spec/recovery before implementation.
- [x] Add direct parser tests for Stryker/mutmut normal, no survivors, incomplete, tampered totals, malformed oversized, no valid mutants, bounded survivors, threshold decisions.
- [x] Add integration tests for configured mutation report required, gate/advisory behavior, worker no-progress/budget exhaustion, and unchanged read-only defaults.
- [x] Capture expected failing Ubuntu/macOS CI. Tests must actually run (no unittest method shadowing).

### M1 — mutation engine reports
- [x] Implement pure `mutation_report.py` parser and CLI (stdlib only). Never follow report symlinks or leak full source text.
- [x] Connect mutation runner's result with exact observed verifier workspace and checkpoint report. Verify exact-head both OS.

### M2 — bounded autonomy
- [x] Add centrally validated policy defaults and safe optional knobs; stage run budget and no-progress avoidance.
- [x] Honor opt-in mutation quality gate before proposing shipping; include detailed verdict and provenance.
- [x] Verify full suite both OS, including all previous 193 tests.

### M3 — 3-pass self-review & handoff
- [x] Review independent code and plan for ambiguous mutation statuses / wrong math.
- [x] Review code for path traversal, budgets, stage reuse, false shipping claims.
- [x] Review UX/docs/help/compatibility; fix, add tests, rerun.
- [x] Commit a bounded self-audit, final exact-head CI and draft stacked PR. **No merge/push to main/release**.

## Recovery / interruption

1. Inspect PR #19 and `feature/mutation-autonomy-v1-20261017`; compare true branch SHA, PR base and CI for *exact current head*. 
2. Read this file before touching code. Begin first unfinished checkpoint; never skip failing tests or treat older green CI as current.
3. Collect source/test/log receipts and maintain final state here. Stored scratch checkpoints are descriptive **not runnable resumptions**.
4. Do not run actual paid agent or mutation tool from CI. Synthetic test repos and hand-authored JSON only; host/SSD acceptance needs owner approval.
5. Keep PR draft; no release automation or protected branch updates.

| Phase | Commit | CI proof | Status |
| --- | --- | --- | --- |
| M0 | 1567ef8e | [Intentional red tests before implementation](https://github.com/raiseCatError/freview/actions/runs/39017038480) | Complete |
| M1 | c06822c5 | [Report parser + stale-report regression Ubuntu/macOS](https://github.com/raiseCatError/freview/actions/runs/39017378141) | Complete |
| M2 | 4caf17d9 / 42dab6e3 | [Standalone consistency](https://github.com/raiseCatError/freview/actions/runs/39017607854), [checkpoint evidence both OS](https://github.com/raiseCatError/freview/actions/runs/39017817033) | Complete |
| M3 | 9fed609b | [Three bounded passes](../audits/2026-10-17-mutation-autonomy-bounded-review.md) + [217 tests, Ubuntu/macOS exact-head success](https://github.com/raiseCatError/freview/actions/runs/39018155210) | Complete as of 9fed609b; this journal update requires its own CI |

## Completion and recovery checkpoint (2026-10-17)

- Test-first M0 red run: https://github.com/raiseCatError/freview/actions/runs/39017038480. The new parser did not exist when tests were committed. Subsequent backward-compatibility failures were investigated and old exit-code-only tests were updated to assert the stronger mutation contract.
- Green code/fixture receipts: M1 https://github.com/raiseCatError/freview/actions/runs/39017378141; M2 https://github.com/raiseCatError/freview/actions/runs/39017607854 and https://github.com/raiseCatError/freview/actions/runs/39017817033. The fake mutmut driver test passed at https://github.com/raiseCatError/freview/actions/runs/39017691880.
- M3 bounded self-review: [three-pass source and evidence review](../audits/2026-10-17-mutation-autonomy-bounded-review.md). Source uses official Stryker report format and verified mutmut exporter details, but never ran a real external mutation engine. `mutmut` CI exporter omits classifications included in its `total`; unclassified counts yield incomplete rather than a guessed score. Unrounded threshold comparisons block false green from rounding.
- All user-controlled programs remain explicit opt-in. Mutation and autonomy are off without policy; shipping is a **handoff only**. Real agent/mutation physical-host and external SSD sandbox acceptance remain unperformed.
- **Final gate:** verify exact current branch SHA and Ubuntu/macOS CI after every documentation commit, update PR #20 acceptance checks; leave PRs #16–#20 in draft and `main` unchanged. No merge, publish, release, install or background task.

## Final confirmation and handoff

- Verified `9fed609bb2f844b994d9e9ae38a45d4401bec85b` at https://github.com/raiseCatError/freview/actions/runs/39018155210: **Ubuntu and macOS jobs both successful**; Ubuntu recorded **217 passing tests**. The two-OS CI jobs provide source/test evidence, **not** proof of real mutation engine performance or independent agent review.
- Stacked PRs #16, #17, #18, #19, #20 verified **draft and unmerged**; `main` unchanged at `2646e4c35e2383b108a752893d846cd48989f2a8` at time of inspection.
- This final journal amendment itself changes the branch HEAD: check the workflow for the newer exact SHA and update PR #20 once it turns green. No further code edits intended. The **release hold remains active** pending separate human approval and real provider/host mutation tests.
