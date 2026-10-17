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
- [ ] Commit failing tests for benign test artifacts, reviewer source modification isolation, file-mode/empty-dir fingerprint changes, mutation side effects.
- [ ] Record exact-head deliberately failing CI.

### Q1 — code fixes
- [ ] Implement stage-specific clones for tests/review/regression/mutation, strict target fingerprint check and provenance.
- [ ] Adjust docs and preserve backward-compatible report fields.
- [ ] Verify exact-head Ubuntu + macOS CI. Do not advance on red.

### Q2 — hygiene and self-review
- [ ] Audit subprocess/file/checkout lifecycle for cleanup and false status claims.
- [ ] Add cross-platform negative fixtures for errors.
- [ ] Run final exact-head CI, record any remaining blind spots.
- [ ] Leave stacked PR draft and preserve `main` unchanged.

## Recovery

Check PRs #16, #17, #18, and the new branch. Fetch actual branch HEAD and latest GitHub Action runs, not prior assistant summaries. Continue at first incomplete checkpoint; update this journal only after verifying. Do not copy tests to Mac or infer the user's local SSD mount from CI paths.

| Gate | Commit | Evidence | State |
| --- | --- | --- | --- |
| Q0 | pending | deliberate failing fixtures | in progress |
| Q1 | pending | GitHub Actions both OS | not started |
| Q2 | pending | final exact SHA and review | not started |
