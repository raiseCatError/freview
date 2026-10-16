# freview audit evidence archive

An evidence log, **not a list of software features or an endorsement of any agent report**.

| Audit | Observation | Scope and caveats |
| --- | --- | --- |
| [Historical freview-on-freview audit (draft PR #8)](https://github.com/raiseCatError/freview/pull/8) | AGY 1.4.0 / Gemini 3.8 Flash High | Full-mode native source review, verified local helper execution; **manual SKILL.md activation**, not native AGY injection; agent audit marked `partial-audit`. Preserve original baseline and later tested SHA. |
| [Independent cross-review and NMSh field evidence](2026-10-17-independent-cross-review.md) | GPT-6 independent freview source inspection + external AGY NMSh run | Independent source-level findings, evidence reconciliation, explicit disputed claims and deferred hardening gates. No freview skill invoked for the GPT source pass; no independent execution on the user's Mac. |

The NMSh field-test generated four **private physical-host documents** (Markdown/JSON audit, freview product field critique and exact-command manifest). Those documents can include local worktree paths and unreleased project state. They are **not published verbatim** to the public repository; the cross-review provides a bounded, privacy-conscious summary instead.

Separate physical reports, GitHub receipts, source observations and agent interpretations. A passing CI job or valid JSON schema is not an execution attestation for a user's local environment.

Future audits should be appended as new immutable records (with exact target, source/skill SHAs, mode, evidence and limitations). Do not silently rewrite an older report to describe a newer implementation.
