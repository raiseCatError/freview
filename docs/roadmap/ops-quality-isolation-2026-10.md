# freview operations quality/isolation review — checkpoints and recovery

Date: 2026-10-17 (Asia/Kolkata)
Branch: `feature/ops-quality-isolation-20261017`
Stacked base: draft PR #18 exact head `03a57244a3b0eca0607dacb52a168bf70cb4c26d`.
Release hold: **no merge, publication, tags, hook installation or provider invocations**.

## Goal

Maintain freview's read-only default and opt-in execution while improving real-world correctness of the runner and code hygiene. In this review, the current pipeline runs test, mutation, regression and reviewer tools in the same editable directory as the worker. This allows tests to generate caches that falsely mark the implementation as unintegrated; worse, tests and reviewers can unintentionally alter worker source files before later stages. Reviewer's intentional mutations are caught too late. The workspace fingerprint also omits filesystem mode and empty directories.

## Safety and evidence rules

- All existing explicit consent and credentials gates remain. No external providers or paid tokens used in fixtures.
- **Tests first**. Demonstrate the issue with offline failing Git/CI fixtures, then implement a minimal isolated verification workspace in the caller's explicitly approved scratch area.
- A candidate workspace is authoritative for worker changes. Every **test/review/mutation/regression** invocation receives a fresh disposable sibling copy of that candidate at its current fingerprint. Verification side effects stay inside that copy.
- Reviewer writes to the copy are **rejected and reported**, even if the reviewer returns valid JSON; no reviewer edits may alter the candidate or be silently applied. Test caches and generated results in the verification copy do not change the candidate or trigger an `implementation-not-integrated` false positive.
- Record stage candidate-before digest and actual verification workspace before/after digest. Keep existing source SHA distinct from modified scratch identity; do not advertise review approval as attestation.
- Fingerprints include file content and executable modes, directory presence and names; reject unsafe symlinks/special files and cap traversal/bytes. This is **not** an OS sandbox; test programs could still access host paths by other means.
- No automatic deletion of user files or existing scratch data. Newly created stage scratch remains for inspection.
- If output/log or checkpoint is missing, inconclusive is an explicit status, not success.

## Checkpoints

### Q0 — test-first acceptance
- [x] Confirm original branch & three PR states from live GitHub.
- [x] Create stacked isolated branch and commit plan.
- [x] Commit tests before implementation for benign test artifacts, reviewer source modification isolation, file-mode/empty-dir fingerprint changes, mutation side effects.
- [x] Record exact-head red CI, noting its initial failing fixture harness was corrected before trustworthy assertions.

### Q1 — code fixes
- [x] Implement stage-specific clones for tests/review/regression/mutation, strict target fingerprint check and provenance.
- [x] Adjust docs and preserve backward-compatible report fields.
- [x] Verify exact-head Ubuntu + macOS CI at the last implementation checkpoint. See receipts below.

### Q2 — hygiene and self-review
- [x] Audit subprocess/file/checkout lifecycle for cleanup and false status claims.
- [x] Add cross-platform negative fixtures for source edits, cache artifacts, permission changes and recovery provenance.
- [ ] Run final exact-head CI, record any remaining blind spots.
- [ ] Leave stacked PR draft and preserve `main` unchanged.

## Recovery

Check PRs #16, #17, #18, and the new branch. Fetch actual branch HEAD and latest GitHub Action runs, not prior assistant summaries. Continue at first incomplete checkpoint; update this journal only after verifying. Do not copy tests to Mac or infer the user's local SSD mount from CI paths.

| Gate | Commit | Evidence | State |
| --- | --- | --- | --- |
| Q0 | 20ff7a37 / c16416d3 | [Initial red (fixture also had a harness bug)](https://github.com/raiseCatError/freview/actions/runs/39013830028); [corrected tests both OS green](https://github.com/raiseCatError/freview/actions/runs/39014037892) | Complete with caveat |
| Q1 | 3cdde9cb / b3c7af90 | [Ubuntu/macOS 193-test success](https://github.com/raiseCatError/freview/actions/runs/39014263341) | Verified |
| Q2 | 90583e26 + docs | [Bounded audit](../audits/2026-10-17-ops-quality-isolation.md); final exact-head CI still required | Under final verification |

## Q2 review notes

- Verified tests on Ubuntu/macOS at source checkpoint `b3c7af90`: https://github.com/raiseCatError/freview/actions/runs/39014263341. Ubuntu reported 193 tests; the final documentation SHA is a separate gate.
- The initial red run is not advertised as clean behavior-first TDD evidence: the new unittest class initially overrode `TestCase.run`, so the first failure partly reflected a defective test harness. That was corrected at `c16416d3` before trusting results.
- New stage receipts distinguish worker candidate digests from verification copies and flag modifications to original candidate entries. Recovery checkpoint v1 retains backward compatibility using optional verifier provenance keys; old records are still inspectable but cannot supply the newer evidence.
- Read [bounded review findings](../audits/2026-10-17-ops-quality-isolation.md). Remaining gates: review final exact-head CI, then leave PR #19 draft and do not merge/release without explicit authorization. Real provider and hostile OS sandbox tests remain unperformed.
