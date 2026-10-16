# Independent freview review × NMSh field test — 2026-10-17

**Status:** independent, evidence-reconciled **partial audit** and improvement specification, not a certified security assessment. **No freview skill invoked for the independent source pass.**

## Source provenance and scope

- Independent GPT-6 source inspection of [freview at 81411193](https://github.com/raiseCatError/freview/tree/81411193b6d23dac74ecc5097032c622a4cf8403), following the Python `-I` fix in [PR #7](https://github.com/raiseCatError/freview/pull/7).
- AGY self-audit: historical [draft PR #8](https://github.com/raiseCatError/freview/pull/8), corrected report at `41b286a7824bedb3cf285be4ffe139aac48a3015`. Its native Antigravity skill injection **did not activate in that session**; the agent manually read SKILL.md and ran helpers. Distinguish valid manual review from native integration.
- User-provided private AGY NMSh field-test bundle: `nmsh-full-review.md`, `nmsh-full-review.json`, `freview-field-test.md`, `execution-manifest.json`. Conducted on the user's physical Mac with `agy 1.4.0` / Gemini 3.8 Flash High, pinned NMSh HEAD `e888b06a561a753cfda4ec05f1650380f9d347d9` (and additional release refs). **Raw reports are deliberately not committed**, because they contain local paths and worktree inventory.
- Independent GitHub checks: NMSh [PR #390](https://github.com/raiseCatError/notMyShell/pull/390), [PR #392](https://github.com/raiseCatError/notMyShell/pull/392), [PR #357](https://github.com/raiseCatError/notMyShell/pull/357), [issue #355](https://github.com/raiseCatError/notMyShell/issues/355), [failed CI run 38930716614](https://github.com/raiseCatError/notMyShell/actions/runs/38930716614), freview source/tests/CI.
- This document excludes local paths, source snippets that may contain private state, credentials, and full raw NMSh execution manifests. Hosted evidence and owner-provided physical results are **different evidence types**.

## Central lesson: local development is not GitHub state

A local feature may exist only as an untracked file, an unstaged edit, a staged edit, a committed-but-unpublished branch, or a different worktree. A cloud-only audit cannot observe these layers. A local Git snapshot may use **stale remote-tracking refs** and cannot prove a push. Green CI on an old commit is not evidence for a new dirty checkout.

Before concluding a feature is missing or complete, an agent should record:

1. User-requested repository and **actual checkout identity** (remote/forge or common Git directory).
2. Evidence availability: cloud-only, local Git checkout, unborn Git repository, or non-Git source folder.
3. Separate staged, unstaged, untracked, local-commit, cached-upstream, live remote/PR, exact-SHA CI, integration and release states.
4. The precise source SHA(s), local dirty state, inspected files, and explicitly unobservable worktrees.
5. Distinct intended **development**, **integration**, **release** and **publication** bases; never silently substitute `origin/master` for an active stabilization train.

Draft [PR #9](https://github.com/raiseCatError/freview/pull/9) implements the first bounded local-first metadata and skill-guidance slice. It **does not** claim to review untracked source bodies automatically or certify remote publishing.

## Findings reconciled against actual evidence

| ID | Priority | Observation | Evidence status / consequence |
| --- | --- | --- | --- |
| IF-01 | P1 | Branch divergence scans issue many Git subprocesses and default to a potentially unhelpful base | Source-confirmed. NMSh field test observed ~437-commit comparison to a published master while nearer stabilization branches existed. Budget/caching in PR #9; development-base selection must remain explicit and explainable. |
| IF-02 | P1 | Report comparisons call disappeared findings `resolved` without proof | Source-confirmed. [report_tools.py](../../skills/freview/scripts/report_tools.py) uses set difference, not remediation evidence. Rename to `absent_from_new_report` (PR #11). |
| IF-03 | P2 | A valid report schema does not authenticate execution | Source-confirmed, inherent trust boundary. Require evidence provenance and nonempty audited category coverage; code validation must never promise independently executed tests. |
| IF-04 | P2 | Report JSON is fully read before checking the 16 MiB cap | Source-confirmed. PR #11 introduces open-once bounded reads; other file readers may need equivalent race-resistant hardening. |
| IF-05 | P2 | Untrusted work-item/report identifiers can carry terminal controls into Markdown | Source-confirmed. PRs #10/#11 sanitize relevant Markdown outputs. JSON remains private evidence, not safe-to-publish by default. |
| IF-06 | P2 | Full local worktree roots and branch names may leak if reports are published | Source-confirmed. Public-safe redaction/export remains a **separate pending capability**. Preserve raw local reports privately. |
| IF-07 | P2 | Duplicate matching is quadratic, order-dependent, and caps only emitted pairs | Source-confirmed. PR #10 adds a comparison budget, transparency, stdin support and non-closing reference handling. Stable ranked candidate selection remains future work. |
| IF-08 | P2 | Agent doctor could call an installation complete when bundled references were absent | Source-confirmed. PR #11 expands asset checks and enumerates both documented AGY global paths; directory presence still cannot prove native skill activation. |
| IF-09 | P2 | Physical agent compatibility cannot be inferred from CI | Confirmed gap. Haiku account2 natively activated freview; AGY's manual SKILL.md workflow ran successfully but native discovery failed in tested session; Codex/OpenCode paths were present, but activation requires separate receipts. |
| IF-10 | P2 | Native skill activation, local helper success, agent code review and external CI are different | Confirmed by AGY's corrected PR #8 and NMSh field test. Adopt explicit source/tool/SHA provenance and separate activation verdicts. |
| FT-01 | P2 | `duplicates.py` doesn't support `Refs #N` | Source-confirmed general gap; PR #10. **Do not treat `Refs` as proof a feature is implemented**, only a relationship that prevents naive duplicate classification. |
| FT-02 | P2 | `duplicates.py -` didn't accept stdin | Source-confirmed controlled error, not a security crash. PR #10. |
| FT-03 | P2 | NMSh candidate PR baselines and published releases are different | Hosted evidence confirms [v0.19 release PR #390](https://github.com/raiseCatError/notMyShell/pull/390) and [v0.20 release PR #392](https://github.com/raiseCatError/notMyShell/pull/392) remain open; manual acceptance blocks promotion. |
| FT-04 | P2 | Historical NMSh queue-preview CI run failed | GitHub confirms failure on `8a6ac8f7386bf7a4609226e37d10243b227e2f90`, **not** current audited branch HEAD `e888b06a...`. An inferred underlying race needs isolated reproduction; don't record as proven at HEAD. |
| FT-05 | P2 | Open NMSh PRs might have stale bases/overlapping delivery | GitHub showed 34 open PRs, 12 based on release/v0.18.0, but that alone does **not** prove duplicate implementations, wrong stacking or cherry-pick equivalence. Compare actual patch identity and intended integration strategy before any tracking changes. |
| FT-06 | P2 | AGY claimed PR #357 / issue #355 were flagged as duplicates | **Not substantiated by supplied execution manifest**: no NMSh duplicate candidate invocation/input/output there. Current PR #357 references #356/#359, while issue #355 calls #357 a dependency. Treat this specific example as unverified agent inference; the generic `Refs` gap is independently real. |
| FT-07 | P2 | AGY reported agent skill version as PR #8 docs SHA `41b286a` | An enclosing worktree SHA is not necessarily the installed skill package identity. Future receipts should use source ref **and asset fingerprints** separately. |
| FT-08 | P2 | External scratch storage was respected by AGY | Owner-provided manifest says `t7run --check` passed. This is host evidence, not independently executable from GitHub; freview should ask the agent to discover each user's actual storage constraints, never hard-code one person's T7 paths. |

## Planned delivery and acceptance gates

| Stage | Branch / PR | Gate |
| --- | --- | --- |
| Local versus cloud scope, current identity, staged/unstaged/untracked/unborn, other worktrees, provisional remote state | [PR #9](https://github.com/raiseCatError/freview/pull/9) | macOS/Linux exact-head Python tests; physical NMSh read-only smoke later |
| Real work-item relationships, bounded stdin, comparison-budget transparency and terminal-safe candidate output | [PR #10](https://github.com/raiseCatError/freview/pull/10) | fixtures for Refs, stdin, cap and actual terminal controls |
| Truthful report deltas, bounded report reads, UTC, complete installed assets, alternate AGY dirs | [PR #11](https://github.com/raiseCatError/freview/pull/11) | fixtures for disappearing findings, oversized/symlinked reports, missing references and native discovery uncertainty |
| Deferred hardening | separate reviewed PR(s) | evidence type/receipt manifest, user-approved public-safe export, remaining bounded file readers, stable duplicate candidate ranking, total subprocess/output budgets, multi-agent physical activation |
| Release decision | fresh freview-on-freview after integration | exact merged HEAD, clean CI, faithful local/cloud review, no fabricated verification, explicit platform matrix |

No automatic merges, NMSh modifications, releases, tags, cleanup or actions on live agent worktrees are authorized by this report.

## What was NOT verified

- The raw NMSh report's complex source-level claims have not all been reproduced with local physical execution; source inspection and hosted GitHub checks do not authenticate them.
- The private/untracked files of the user's current NMSh worktrees are not observable through this analysis environment.
- No full NMSh release-suite rerun, live TUI/VoiceOver test, third-party paid code review or private security-alert scan has been performed here.
- The intended release-integration strategy for every open NMSh PR is not established solely from their base refs.
- PRs #9–#11 are proposed improvements, **not integrated functionality** until reviewed, merged and tested on actual `main`.
