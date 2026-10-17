# freview ops: evidence-backed review verdicts — recovery & acceptance plan
Date: 2026-10-17. Work branch: `feature/ops-reviewed-verdicts-20261017`.
Stacked base: `feature/opt-in-ops-20261017` at `4ad489ecf14ab5acb564a0deea7a009ae842544b`.
Status: development only. Do not merge, publish, install agents, or alter user worktrees.

## Why this is next

Previous freview optional operations tested command/process exits but **did not interpret adversarial review findings**: an exit code 0 could still conceal a request to change code. Further, a reviewer used the same disposable workspace as the worker and might modify code/tests. The product's promise is "Audit the repo, not the summary"; a reviewer stdout message or successful process exit is a *claim*, never authoritative proof. This tranche closes that workflow gap without creating a competing coding framework.

## Spec and invariants

- Default read-only freview unchanged; all optional modules remain disabled by default. No implicit AI calls or tokens.
- An *enabled and invoked* adversarial reviewer must emit **one bounded JSON object** with explicit schema version, exact original source SHA, exact audited disposable workspace fingerprint, independent reviewer verdict (`approve`, `changes_requested`, `blocked`), and bounded findings. No raw free-form "looks good" accepted. A valid object is a **reviewer-reported claim**, not authenticated model independence.
- Reviewer must get original approved requirements and snapshot identity, **never the worker summary on first pass**. Reviewer must not change the audited workspace. Any mutation, malformed/inconsistent output, report budget overflow, or unobservable evidence blocks approval and shipping.
- For `changes_requested`, run at most three cycles. Feed bounded structured findings back to the worker; rerun tests before a new review. A reviewer process failure alone is **not** a valid reviewed finding and must not cause blind retries.
- Distinguish test success on a worker-modified scratch candidate from verification of original Git SHA. Record source SHA, workspace SHA-256 digest, stage evidence and review observations separately; no automatic source merge, push or release.
- No new providers or third-party vendoring; use generic configured CLI argv. Real Claude/Codex/OpenCode subprocess acceptance requires an explicitly connected host with CLI credentials; GitHub CI fake-agent tests cannot certify that.
- No default shell execution, unknown env forwarding, OS sandbox claims, undocumented disk fallback, or user checkout mutation.
- A validation tool cannot claim the reviewer genuinely read source or ran tests. Separate user-approved sandbox + independent runs remain an additional gate.

## TDD checkpoints

### V0 — precise red tests
- [x] Branch from exact PR #17 head.
- [x] Commit durable plan before code.
- [x] Write tests that fail for missing/invalid JSON verdicts, mismatched SHA or fingerprint, unexpected approval with findings, reviewer mutating workspace, reviewer finding fed back to worker, no blind retry on process failure, cap at three.
- [x] Observe red exact-head GitHub CI for the contract.

### V1 — bounded verdict validator
- [x] Implement stdlib-only `review_verdict.py` with strict validator and schema-v1 description, no execution.
- [x] Verify unit tests plus full Ubuntu/macOS CI, checkpoint SHA.

### V2 — pipeline integration
- [x] Prompt review with original requirements + SHA + workspace digest; review verdict read from **bounded process stdout log**. Worker summary excluded.
- [x] Reject truncated output and same-workspace mutations; act on structured `changes_requested` only. Keep reviewer findings/response evidence referenced in records.
- [x] Tests run on updated scratch candidate after each fix cycle. Surface `reviewer-approved-claim` vs verified tests, not `proven correct`.
- [x] Verify full Ubuntu/macOS CI, checkpoint SHA.

### V3 — durable evidence checkpoints and self-review
- [x] Test-first: every completed pipeline stage emits a bounded atomic recovery manifest in caller-selected scratch, and inspection is non-executing.
- [x] Never automatically resume, skip checks, or trust a checkpoint as attestation; missing/corrupt/oversized/symlinked checkpoints fail closed.
- [x] Implement stage checkpoint writer, inspection CLI, and verify synthetic fixture in Ubuntu/macOS.
- [x] Inspect changed source/test/docs for hidden edge cases and false-confidence outputs.
- [x] Offline fake worker/reviewer tests in `tests/test_review_verdict.py` (no external token usage or network), plus checkpoint tests (no token usage, no network) that exercises three-round loop and negative receipts.
- [ ] Verify both GitHub CI runners at **final exact SHA**. Leave stacked PR draft, no merge, release or tagging.

## Recovery

1. Read this file, `docs/roadmap/optional-ops-2026-10.md`, and parent PRs #16 and #17.
2. Fetch `feature/ops-reviewed-verdicts-20261017` and its CI jobs by exact `head_sha`.
3. Pick first unchecked checkpoint. Do not reuse older green CI as evidence of a newer commit.
4. No arbitrary host code/agents should run in CI. If an external runtime cannot be reached, report *not observed*, never pass.
5. Preserve all work in PR; run status is in Git/CI, not assistant claims.

## Checkpoint receipts
| Stage | Commit | Evidence | State |
| --- | --- | --- | --- |
| V0 | 3a8d1cf4 | [Intentional red CI](https://github.com/raiseCatError/freview/actions/runs/38995811988) | Complete |
| V1 | 02cc70ee | Validated with V2 full suite at c48a0747 | Complete |
| V2 | c48a0747 | [Ubuntu/macOS CI](https://github.com/raiseCatError/freview/actions/runs/38996154454) | Complete |
| V3 | 41cec484 | [Ubuntu/macOS V3 code CI](https://github.com/raiseCatError/freview/actions/runs/38996474987); [bounded self-review](../audits/2026-10-17-structured-review-and-checkpoints.md) | Code/tests complete; final docs-head CI pending |

## Checkpoint update (2026-10-17)

- V0 intentionally red at `3a8d1cf4`: https://github.com/raiseCatError/freview/actions/runs/38995811988. Test specification preceded production validator.
- V1 validator `review_verdict.py` added `02cc70ee`; pipeline integration `7856fac2`, then regression fixes `39a47790` and independent reviewed-file-path existence check `c48a0747`.
- **V2 exact-head successful Ubuntu+macOS:** https://github.com/raiseCatError/freview/actions/runs/38996154454 at `c48a074706c814b48fc102ca32c58cb34569d7e1`. This is offline fake-reviewer CI, not real independent Claude/Codex/Opencode invocation.
- Additional V3 checkpoint tests/implementation are next. Retain stacked draft PR #18. Any later CI must match its new exact head; prior success is not enough.

## Final V3 checkpoint note

- Structured review output alone cannot prove separate model identity. The reviewer-approved state is named `reviewer-approved-claim` and all independence fields stay false. A reviewer subprocess error doesn't trigger blind retries, only grounded `changes_requested` findings with an enabled worker do.
- The scratch checkpoint is **not resumable executable state**. `inspect-checkpoint` is bounded, read-only, rejects forged metadata and does not skip or repeat stages. Full rerun is required for a fresh candidate SHA after interruption.
- A macOS test was corrected to resolve `/var` versus `/private/var`; the source uses approved canonical scratch. Security/source review is [here](../audits/2026-10-17-structured-review-and-checkpoints.md).
- **Release hold remains active**. PR #18 stacks on draft #17 which stacks on draft #16; none should merge, tag or publish autonomously. Final exact-head Ubuntu/macOS run and manual owner review remain required.
