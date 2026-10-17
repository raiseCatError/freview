# freview-on-freview: mutation and autonomy v1 bounded review

**Date:** 2026-10-17. **Scope:** stacked draft PR #20 over #19. 
**Method:** one bounded GPT source/test-contract review in three passes, GitHub Actions Ubuntu/macOS deterministic fixtures. **Not** three independent models or a real mutmut/Stryker mutation campaign.

## Product question

Does freview make *opt-in mutation and autonomous repair safer, measurable, configurable and not misleading* while remaining a read-only repository auditor by default?

**Answer from bounded evidence:** yes for the deterministic report/runner semantics and synthetic fixtures. Real provider/mutator reliability, survivor usefulness, OS sandbox behavior and protected release mechanics remain unobserved.

## Pass 1 — mutation score and real tool compatibility

- Consulted [Stryker official mutant states](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/) and the [mutation-testing-elements report schema](https://github.com/stryker-mutator/mutation-testing-elements/blob/master/packages/report-schema/src/mutation-testing-report-schema.json): Killed/Timeout = detected; Survived/NoCoverage = undetected; Pending makes report incomplete; ignored/error mutants are not counted as valid.
- Implemented a stdlib-only, size-bounded, duplicate-key-safe parser and fixed report discovery; includes bounded survivor path/line hints without copying report source. Zero valid mutants or missing/ambiguous/oversized/symlinked reports cannot pass. Score thresholds compare the **unrounded** numerator, avoiding an accidental pass at rounding boundaries.
- Independently inspected [mutmut implementation](https://github.com/boxed/mutmut/blob/main/src/mutmut/__main__.py): its `export-cicd-stats` includes a `total` whose components may include **unexported** `not_checked` and `caught_by_type_check`. Instead of inventing categories or rejecting every real report, we mark the difference `unclassified` and **incomplete**. Tests cover interrupted, suspicious, unknown and inconsistent totals.
- Added `mutmut_driver.py` to run already-installed `mutmut run` and export the supported CI JSON without invoking a shell. Fake executable tests prove command sequencing and fail-closed missing export; no real engine installed or executed here.
- **Limit:** a successful scored report is not proof tests cover intended behaviors, and native mutation generation was not exercised.

## Pass 2 — autonomy loops and evidence gates

- Configurable, bounded `autonomy.max_stage_runs` (default 12, hard max 32) limits total invoked stages, with timeout/output limits per stage and max 3 review rounds.
- On actionable review findings, stop if the worker makes no candidate source change; also stop if the exact finding signature repeats despite unrelated edits. Both stop conditions are regression-tested.
- Mutation command exit code zero alone **cannot pass** even in advisory mode. Both `run mutation` and `pipeline` now require a newly written report in the disposable mutation verifier workspace. A committed stale report cannot be credited to the current run; incomplete, missing or malformed report blocks. The optional `gate` mode requires configurable minimum valid mutants and score.
- `require_mutation_for_shipping` can be enabled to require a quality passing mutation check before producing even a **handoff-only** shipping checklist.
- Mutation score/counts and fresh-report observation are persisted in atomic, read-only scratch checkpoints. Checkpoints are **not** signed execution attestations and do not automatically resume commands.
- **Limit:** stage and report identifiers are still local metadata, not cryptographically trusted, and the verification copy is not an OS sandbox.

## Pass 3 — integration, UX, regressions and release gates

- Old tests that expected success from a mutator's zero exit were updated to correctly expect `mutation-inconclusive`; earlier three-loop fixtures were updated for no-progress stop. Initial red CI tested missing modules, then later CI caught integration and schema assumptions. No green state was inferred from older test runs.
- `examples/freview-ops.example.json` explicitly documents the new controls with every module still disabled, and the README/SKILL/optional ops manual link to a detailed [mutation/autonomy guide](../../skills/freview/references/mutation-autonomy.md).
- CI includes the new scripts in compilation checks and static bundled-file tests. No third-party source code was copied; all shipped scripts use the Python standard library.
- **Release hold:** draft PRs #16–#20 are not merged; `main` remains untouched. No real paid reviewer or mutmut/Stryker run, external SSD smoke, remote shipping, branch-protection configuration or installation performed in this cycle.

## Evidence

- Deliberate test-first red run: https://github.com/raiseCatError/freview/actions/runs/39017038480.
- Corrected legacy semantics green: https://github.com/raiseCatError/freview/actions/runs/39017271191.
- Stale-report provenance fix green: https://github.com/raiseCatError/freview/actions/runs/39017378141.
- Standalone mutation and mutmut fake runner integration green: https://github.com/raiseCatError/freview/actions/runs/39017691880.
- Mutation checkpoint summary schema green: https://github.com/raiseCatError/freview/actions/runs/39017817033.
- Packaged skill and policy default example green: https://github.com/raiseCatError/freview/actions/runs/39017925557.
- **Final exact-branch-head CI still needs to be fetched and verified after this document and checkpoint journal commits.** Older greens do not certify later heads.

**Verdict:** scoped feature and code-quality work complete pending final exact-head CI. No basis to claim authenticated multi-agent autonomous shipping or actual mutation engine score on a production repository. User confirmation is required before merging stacked PRs or running connected tools on a real checkout.
