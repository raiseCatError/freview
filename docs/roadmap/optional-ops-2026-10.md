# freview optional operations — specification, test plan and recovery journal

Date: 2026-10-17 UTC
Branch: `feature/opt-in-ops-20261017`
Stacked base: evidence-reconciliation PR #16 head `e42ff2d554b96ff6f5c0bd7c4926f242ce1e4d80`
Status: development; no release or merge authorized.

## Product boundary

**Audit the repo, not the summary.** Read-only freview is the product and remains the default. An optional, explicitly configured **freview ops** companion coordinates specification, planning, test execution, independent reviews, regression sensitivity, mutation, hooks and proposed shipping. It is NOT a code-review replacement, a universal agent framework, a sandbox/security boundary, a fully automatic GitHub merge bot, or proof that tests are adequate.

The user requests an on/off/toggleable system with minimal unnecessary tokens. Keep one central policy, no silently installed tools, no broad default agent prompts, max three review rounds, reusing receipts when identical tree + command match, bounded logs and explicit unknown outcomes.

Competitor design references (no external code copied):
- **GitHub Spec Kit / OpenSpec**: requirements with testable scenarios and tasks; implement *interoperable* Markdown/JSON evidence plan, not a new DSL.
- **GSD / gstack / Superpowers**: staged plan → implement → review → verify → ship, durable resumable checkpoints, context efficient agents.
- **Nonna**: optional test and protected branch enforcement; make hook installation *explicit*, chain rather than overwrite existing hooks or decline.
- **agent-review-skill / review-loop**: independent reviewer fresh context and bounded challenge loops (max 3); no model-claims-as-proof.
- **Stryker / mutmut**: mutation delegated to vetted user-selected tool; test-quality and baseline sensitivity separate from passing tests.
- **freview base**: local/remote evidence reconciliation and report contract remain authoritative.

## Hard defaults and permissions

1. No ops policy = status / dry-run only, **nothing executed**. No hooks, no test/mutation/reviewer calls, no commits/pushes.
2. Explicit, schema-versioned repo-local `.freview-ops.json` permits individual modules. Command argv arrays, no shell, no dynamic interpolation of user-controlled text. All user-supplied paths are untrusted. Never execute a workflow merely because a repo file says to.
3. Every mutating or code-execution invocation also requires a CLI confirmation flag, trusted checkout assessment and explicit writable scratch directory. This is **not a security sandbox**; malicious tests can still access OS/network unless run in a true external sandbox.
4. Dedicated scratch outside the source tree, no fallback to home/internal temporary storage; verification of policy's scratch mount is the user's responsibility, check resolved path and disallow scratch inside checkout. Clean committed worktree requirement for immutable SHA verification; dirty tree explicitly blocks run.
5. No automatic merge, protected-branch push, public release, deployments or network-uploading agents. Shipping produces a verified dry-run checklist/handoff by default; actual release needs separate user authorization and an external release system.
6. Budget execution time, output bytes, number of rounds and spawned programs; no automatic `pip/npm/brew` installs. Treat exit codes and logs as observations, reviewers as claims, mutation survivors as potential coverage issues, baseline failures as inconclusive when incompatible.
7. Maintain versioned deterministic evidence receipts and privacy warnings; never claim **independent** review just because command labels say so.

## Checkpoints (TDD-first)

### P0 — specification and tests FIRST
- [x] Create isolated branch from PR #16 at exact SHA.
- [ ] Commit this durable plan before code.
- [ ] Add tests asserting default-off, schema/argv guardrails, branch protection, three-pass cap, scratch isolation, exact SHA, optional command invocation, code/test quality outcomes, no non-opted mutations.
- [ ] Verify *red* initial CI for tests that refer to unimplemented ops module; record run URL.
**Gate:** tests express accepted behavior before implementation, no accidental mainline change.

### P1 — policy, status and plan (non-executing)
- [ ] Implement readable, bounded config with defaults; dry-run status and structured plan/checkpoints, tested against fixture.
- [ ] Verify exact-head Ubuntu/macOS CI.
**Gate:** read-only defaults, no secrets or arbitrary project execution; checkpoint commit.

### P2 — independent verification and optional runners
- [ ] Explicit opt-in runner for test command, reviewer programs, mutation tool, regression sensitivity. Strict argv, fixed caps, expected SHA, scratch copy, exit+log evidence, actual statuses; logs only in approved scratch.
- [ ] Use independent reviewer context separated from worker text; reviewer responses do not certify correctness.
- [ ] Verify exact-head CI and test fake stubs only; do not call paid or unauthenticated agents on CI.
**Gate:** no protected ref mutations; output receipts distinguish missing/failed/reproduced claim vs reality.

### P3 — optional hooks and shipping handoff
- [ ] Install hooks only on explicit request; never clobber existing hook; verify branch and configured checks; safe uninstall preserving others.
- [ ] Spec/plan → implementation/review/verify pipeline with meaningful controls. Policy-managed shell-free subcommands, stage attestations and human handoff.
- [ ] Shipping by default emits release checklist; no automatic push/merge/release.
- [ ] Verify exact-head CI.

### P4 — three bounded self-review iterations
- [ ] R1: review implementation vs original specification without relying on worker summary; fix+test.
- [ ] R2: adversarial audit security/edge cases/compatibility; fix+test.
- [ ] R3: release/readiness audit and tests; fix+test.
- [ ] Record exact-SHA evidence and limitations for each; maintain no release hold.
- [ ] Draft stacked PR targeting `feature/evidence-reconciliation-20261017`, no merge or publish.

## Recovery instructions

Fetch and inspect both PR #16 and this branch, the latest CI status for **exact head**, current plan and its checkpoint log. Continue at first incomplete gate. Never infer a green status from an older SHA. Source truth = GitHub refs, tests and CI, not agent's final narrative. Do not advance through failing CI. Avoid destructive worktree cleanup. Scratch paths should obey the consumer project's storage policy.

## Checkpoint log

| Stage | Git SHA | Proof | Status |
| --- | --- | --- | --- |
| P0 | pending | red tests and documented specification | in progress |
| P1 | pending | tests, Ubuntu/macOS CI | not started |
| P2 | pending | tests, Ubuntu/macOS CI | not started |
| P3 | pending | tests, Ubuntu/macOS CI | not started |
| R1-R3 | pending | exact SHA, scope, fixes/limits | not started |
