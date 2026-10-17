# freview-on-freview — verifier isolation and code hygiene

**Date:** 2026-10-17. **Status:** bounded review, draft PR #19 stacked on draft PR #18.
**Evidence classification:** hosted source inspection + reproducible local Git/Python **CI** fixtures on Ubuntu/macOS, not an authenticated second model, real mutation campaign, physical Mac QA, or a formal security assessment.

## Review scope

The review examined the optional operations runner's candidate-workspace lifecycle, stage execution, checksum provenance, source-integrity assumptions, checkpoint reporting and shell-free hook/CLI integration. Original product intent is **Audit the repo, not the summary**. All optional modules remain OFF by default. No production source worktrees or external SSDs were touched; no paid agent/test runner installed; no main-branch merge, tag, deployment or publication performed.

## Confirmed defects and corrections

| Finding | Before | Correction / regression |
| --- | --- | --- |
| **Test-generated cache contamination** | Tests ran inside the worker's mutable candidate tree. Generated caches could trigger `implementation-not-integrated` for otherwise unchanged source. | Every test gets a fresh disposable verifier copy of the candidate; new caches remain in that copy. `test_test_generated_cache_does_not_poison_candidate_or_shipping` |
| **Test-induced source mutation** | A test command could rewrite existing worker-source files, altering subsequent checks in the same directory. | Existing candidate source files/permissions are compared against the test copy after execution; `tests-mutated-source` is a blocking outcome. `test_test_that_overwrites_source_is_not_a_valid_gate` |
| **Reviewer-induced cross-stage changes** | A reviewer might alter the candidate before the next worker or test. | Reviewer gets a fresh copy; *any* mutation of that copy rejects the review, and no modification is carried into the worker candidate. `test_review_mutates_own_copy_not_worker_candidate` |
| **Mutation tool side effects** | Mutation tool's writes were able to contaminate the candidate. | Mutation and external regression stages now use isolated copies. Mutation-output files remain available only in the associated verifier copy and private logs; no mutation score is inferred from process exit. `test_mutator_side_effects_do_not_contaminate_candidate` |
| **Incomplete workspace identity** | Fingerprint accounted for file names/content but not executable mode or empty directories. | Bounded canonical inventory includes names, modes, contents and directory entries. Tests verify mode-only and empty-directory changes produce different identities. |
| **Ambiguous recovery evidence** | A stage's checkpoint digest could refer to artifacts produced by testing rather than the original candidate. | Checkpoints report **current candidate digest** plus optional verifier-path, verifier-candidate digest and source-modification flags, with strict shape validation and no auto-resume. |
| **Dead code** | Unused `io` import and identifier regex in ops module. | Removed without changing public API. |

## Test-first evidence and limits

Tests were added before the implementation changes, with an intentionally red initial PR run. **Important correction:** the initial test fixture accidentally named a helper `run`, overriding `unittest.TestCase.run`, so the first red result was partly a *test-harness defect*, not an authentic clean demonstration of every intended failure. The fixture was corrected before using its outcome as evidence.

The complete suite then passed on Ubuntu and macOS at `c16416d3` (https://github.com/raiseCatError/freview/actions/runs/39014037892), at the full provenance changes `3cdde9cb` (https://github.com/raiseCatError/freview/actions/runs/39014172104), and after source cleanup `b3c7af90` (https://github.com/raiseCatError/freview/actions/runs/39014263341). The latter Ubuntu job reported **193 passed tests**. **The final documentation-head CI must be verified separately after all commits.**

## Remaining risks and performance tradeoffs

- This copies a bounded source candidate for each executed test/reviewer/regression/mutation stage, using **caller-approved scratch storage only**. It uses more disk I/O and scratch space than in-place verification, by design. Retained run copies support investigation; explicit user cleanup policies and quotas would be useful later. Do not remove any existing user worktree or scratch run automatically.
- A test or reviewer with full host permissions may still access other filesystem paths, the network or the original repository outside its copy. These helpers are **not OS security sandboxes**. Concurrent hostile filesystem modification can race inspections; all results need a threat-appropriate sandbox before executing untrusted code.
- Generated **new files** in a test copy are permitted, but changes to *existing* candidate entries are blocked. This can flag legitimately source-modifying test tools; such a workflow needs explicit owner evaluation, never silent allowlisting.
- A passing process exit is not proof tests executed meaningful assertions. A mutation program exiting zero proves only execution status. A reviewer-approved JSON receipt remains a claim and does not authenticate separate provider identity, actual source reading, or independent test reproduction.
- Source fingerprints are SHA-256 metadata snapshots, not signed attestations, canonical Git tree SHAs or protections against malicious processes that modify and restore files between observations.
- Real Claude/Codex/OpenCode CLI acceptance, authenticated multi-agent evaluation, mutation survivors, and protected remote release workflows were not run in this review.

## Disposition

**Scoped correctness and hygiene fixes implemented with regression coverage**. No new confirmed functional blocker remains from this bounded inspection as of its last source-checkpoint CI. That is not a certification of defect-free software. Preserve PRs #16–#19 as draft and require owner review, controlled external-scratch smoke test and verified final exact-head CI before any merge/release.
