# freview audit evidence archive

An evidence log, **not a list of software features or an endorsement of any agent report**.

| Audit | Observation | Scope and caveats |
| --- | --- | --- |
| [Historical freview-on-freview audit (draft PR #8)](https://github.com/raiseCatError/freview/pull/8) | AGY 1.4.0 / Gemini 3.8 Flash High | Full-mode native source review, verified local helper execution; **manual SKILL.md activation**, not native AGY injection; agent audit marked `partial-audit`. Preserve original baseline and later tested SHA. |
| [Independent cross-review and NMSh field evidence](2026-10-17-independent-cross-review.md) | GPT-6 independent freview source inspection + external AGY NMSh run | Independent source-level findings, evidence reconciliation, explicit disputed claims and deferred hardening gates. No freview skill invoked for the GPT source pass; no independent execution on the user's Mac. |
| [Post-integration exact-head verification](2026-10-17-integration-receipt.md) | Combined `main` at `3870b786` | Four PRs integrated; 93/93 Python tests on both Ubuntu and macOS with exact-head CI; real native-agent activation remains pending. Includes a [physical acceptance checklist](../testing/agent-activation-acceptance.md). |
| [Final pre-release self-review](2026-10-17-final-pre-release-self-review.md) | Source baseline `b4e9de58` after PR #14, plus this hygiene PR's documentation | Hosted GitHub evidence and bounded GPT-6 native source read; **partial-audit**, not in-session activation of installed freview. Public-safe summary of owner-reported AGY/Claude/Codex/OpenCode activation, exact-head CI, known boundaries and deliberately paused release. |
| [Evidence reconciliation C1–C4 self-review](2026-10-17-evidence-reconciliation-self-review.md) | Draft PR #16, based on `2646e4c3` | Bounded hosted source review of spec inventory, metadata receipts, claim delta schema and adversarial fixtures. **Not an independent second-agent audit**; final exact-head CI must be checked separately; publication held. |
| [Optional ops three-pass bounded review](2026-10-17-optional-ops-three-pass-self-review.md) | Stacked draft PR #17, test-first development, three bounded review–fix–CI cycles | Host-side source inspection and synthetic Ubuntu/macOS test evidence. **No actual independent second model, mutation run, native installed-agent QA or autonomous publication.** |
| [Structured reviewer verdicts and scratch recovery self-review](2026-10-17-structured-review-and-checkpoints.md) | Stacked draft PR #18, checked against PR #17 at `4ad489ec` | Test-first source review, verified synthetic reviewer JSON protocol, recovery manifest and three bounded verification gates. **No real independent model activation or automatic release.** |
| [Verifier isolation and code hygiene](2026-10-17-ops-quality-isolation.md) | Stacked draft PR #19 above #18, Ubuntu/macOS synthetic Git fixture evidence | Fixed test-cache contamination, source-write isolation, mode-aware workspace identities and verifier-copy provenance. **No independent external model invocation or OS sandbox certification.** |

The NMSh field-test generated four **private physical-host documents** (Markdown/JSON audit, freview product field critique and exact-command manifest). Those documents can include local worktree paths and unreleased project state. They are **not published verbatim** to the public repository; the cross-review provides a bounded, privacy-conscious summary instead.

Separate physical reports, GitHub receipts, source observations and agent interpretations. A passing CI job or valid JSON schema is not an execution attestation for a user's local environment.

Future audits should be appended as new immutable records (with exact target, source/skill SHAs, mode, evidence and limitations). Do not silently rewrite an older report to describe a newer implementation.
