# freview-on-freview: structured reviewer and recovery hardening audit

**2026-10-17 — stacked draft PR #18.**
**Review type:** bounded GPT source/diff inspection with executable **Ubuntu/macOS GitHub CI**. No actual separate Claude/Codex/OpenCode provider invoked; **not** an authenticated adversarial multi-model self-review, mutation campaign or runtime security audit.

**Base:** `feature/opt-in-ops-20261017` at `4ad489ecf14ab5acb564a0deea7a009ae842544b`.
**Change:** strict `review_verdict.py`, audited workspace-source binding in `ops.py`, atomic non-resuming `checkpoint.json`, negative contract fixtures, documentation.
**Product premise:** **Audit the repo, not the summary**. Do not turn a reviewer stdout string, JSON object or subprocess exit code into proof of correctness.

## Test-first review, corrections and checkpoints

### Pass A — review contracts vs actual runner

- **P0 (intentional red):** `3a8d1cf4`, [CI run](https://github.com/raiseCatError/freview/actions/runs/38995811988). Tests demanded explicit review verdict and mismatch rejection before production code existed.
- **Issue found:** the prior pipeline retried a reviewer executable with a nonzero exit up to three times, wasting tokens with no grounded repair instructions. **Correction:** treat process failure as blocked immediately; cycle only on validated `changes_requested` with a configured worker, handing over bounded structured findings and rerunning tests. No worker = no pointless retries.
- **Issue found:** earlier fixture searched for human prose instead of the actual JSON feedback. **Correction:** assert a structured finding reaches the worker and a subsequent review can report a different observation.
- **Issue found:** a fake review could claim to have inspected a nonexistent file. **Correction:** check cited source paths actually exist within disposable audited workspace; this still cannot prove actual source reading.
- **V2 exact source CI:** [Ubuntu/macOS passed](https://github.com/raiseCatError/freview/actions/runs/38996154454) at `c48a074706c814b48fc102ca32c58cb34569d7e1`.

### Pass B — resource, input and privacy boundaries

- Strict JSON, no duplicate keys, version types, no unknown fields, exact source SHA + workspace SHA-256, bounded findings and paths, zero findings for an approval, specific evidence for `changes_requested`. Malformed or truncated outputs fail closed.
- Reviewer writes to source workspace are rejected via pre/post fingerprint, with the existing caveat that a malicious process can edit and restore contents undetected absent an OS sandbox. A valid verdict is labeled `approved-claim` with `reviewer_independence_verified=false`, `source_reading_verified=false`, `test_quality_verified=false`.
- Closed subprocess stdout descriptors observed as `ResourceWarning` under CI; no output or command secret should be duplicated in public audit reports.
- **Unperformed:** real provider/model independence and any mutation engine, physical host filesystem sandbox, malicious reviewer threat-model penetration test.

### Pass C — interruption safety and status inspection

- Test-first checkpoint cases require a durable, private, atomic, bounded manifest in explicitly selected scratch, including both failed and successful runs, and a read-only inspector that **never** replays commands.
- **macOS fixture failure:** `/var` resolves to `/private/var`; corrected the path test to compare canonical paths, leaving the implementation's canonical scratch behavior intact. [CI success](https://github.com/raiseCatError/freview/actions/runs/38996409486) at `d75be5c1`.
- Negative fixtures rejected forged `attested`, `resumes_execution`, corrupted exact SHA/digests, invalid stage receipts, and oversized/symlinked records. The manifest cannot create an independently reproduced test status; it is descriptive.
- **V3 code CI:** [Ubuntu/macOS passed](https://github.com/raiseCatError/freview/actions/runs/38996474987) at `41cec484786d2663411158f4d3b0bf07da6f1394`.
- Final docs HEAD: verify **after** last documentation commit; no inference from old green runs.

## Functional coverage and deliberate boundaries

| Capability | Established | Not established |
| --- | --- | --- |
| Fresh reviewer subprocess | Configured argv + independent process lifecycle in fake local tests | Different provider/account, authenticated reviewer identity or source actually read |
| Explicit JSON review conclusion | Format, exact SHA and disposable digest consistency, bounded findings | Truth of reported findings or adequacy of coverage |
| Automatic bounded repair loop | Structured actionable findings, worker feedback, tests each round, max three | Safe autonomous merge of generated code |
| Local scratch fingerprint | Observed file content identity and reviewer-change detection | OS sandbox, signed evidence or defense against transient revert |
| Recovery manifest | Atomic structured status after stages, strict inspector | Automatic resumability, remote durability or signed attestation |
| Multi-stage orchestration | Policy-gated worker/test/reviewer plus optional mutation/regression stages | Authentic external model, mutator and CI-provider end-to-end runs |
| Release readiness | No automated push, merge, tag or release | Server-side enforced merge protections/authorized deployment |

## Reviewer disposition

**No confirmed blocker found in the bounded source-contract audit after these corrections.** This is *not* a claim that the codebase is defect-free. PR #18 should remain **draft**, stacked on #17 and #16, with all three unmerged. No release was created.

Recommended next authorized host acceptance: run explicit provider wrappers (Claude, Codex and OpenCode) with intentionally invalid/valid reviewer outputs and no inherited secrets; test against a realistic project in an OS sandbox and approved external scratch, inspect private stage logs and synthetic mutation survivors; then decide whether provider adapters, real commit integration and a protected GitHub App merge-gate are justified. Never automatically enable expensive external agents for a routine Standard audit.
