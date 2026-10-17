# freview reviews freview — final pre-release evidence review

**Recorded:** 2026-10-17 UTC  
**Audit classification:** `partial-audit` — bounded independent source review plus read-only hosted GitHub verification.  
**Repository:** [raiseCatError/freview](https://github.com/raiseCatError/freview)  
**Source baseline checked:** `main` [`b4e9de581107b8b78b4a710a5be93fa4e90510e8`](https://github.com/raiseCatError/freview/commit/b4e9de581107b8b78b4a710a5be93fa4e90510e8) (merged [PR #14](https://github.com/raiseCatError/freview/pull/14)).  
**Documentation scope:** this subsequent pre-release hygiene branch adds issue/PR templates and updates the audit index and README; its exact-head CI must pass separately.  
**Review approach:** GPT-6 native, bounded source inspection using the GitHub connector, following freview's evidence and permission rules. **This was not native installed `/freview` or `$freview` activation in this GPT session.** No official specialist review, user workstation access, test execution or physical accessibility test was performed by this reviewer.

## Verdict

**Ready for a read-only preview on trusted repositories, with documented limitations; publication deliberately paused.** The original issue/PR and code-review findings were addressed through merged [PRs #9–#14](https://github.com/raiseCatError/freview/pulls?q=is%3Apr+is%3Amerged) and the integrated current baseline has green exact-SHA Ubuntu/macOS CI. This is **not** approval to tag, publish, deploy, run unattended against hostile code, or claim screen-reader/security certification.

A passing workflow, a schema-valid report, a locally installed skill and a native skill invocation are four different kinds of evidence. They do not substitute for one another.

## Review scope and source provenance

| Category | Evidence inspected | Classification |
| --- | --- | --- |
| Repository and delivery | Live GitHub `main` SHA, merged PRs #9–#14, historical draft PR #8, current issues and PR inventory | **Verified hosted metadata** for requested repo; local-only changes not observable |
| Code and tests | `skills/freview/SKILL.md`, five Python helper implementations, relevant test assertions, six test modules, CI workflow and report/config guidance | **Bounded independent source read**; no claimed complete line-by-line security audit |
| Local-first Git | `repo_snapshot.py` staged/unstaged/untracked/worktree and cached-upstream code, associated fixture names and reviewed prior reports | **Source reviewed**; physical checkout and unpushed user work not inspected |
| Duplicates | `duplicates.py` explicit issue/PR relationship logic, candidate-only output, comparison/emit caps and regression tests | **Source reviewed**; no independent runtime fixture execution |
| CLI/report trust | `review.py`, `report_tools.py`, `agent_doctor.py`, bundled schema, config/activation docs | **Source reviewed**; metadata is not attested execution |
| CI | [GitHub Actions 38983887532](https://github.com/raiseCatError/freview/actions/runs/38983887532) at exact `b4e9de58` | **Verified hosted result:** 99/99 tests, Ubuntu and macOS; current hygiene branch needs its own CI |
| Release status | GitHub release inventory and tag refs | **Verified:** none published or tagged at review time |
| Community | `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, accessibility note, newly proposed issue/PR templates | **Reviewed**; repository description remains blank |
| Dependencies | Standard-library Python helpers and declared workflow dependencies (pinned Actions) | **Limited**; no package vulnerability scanning or dependence on a fabricated package lock |
| Accessibility/security posture | Control-character escaping, privacy-warning guidance, opt-in scanner policy and documented physical QA | **Partial:** no physical VoiceOver/NVDA run and no external security scan |

### Code-path reconciliation

- **Integrated functionality:** local-first status, wrong-repository optional identity guard, cautious cached-upstream state, bounded worktree inspection, explicit issue/PR duplicate *candidates*, controlled report comparisons, privacy-lint warnings and static multi-profile agent doctor exist in `main`. The local helper still emits `local-snapshot` even when requested mode is Full; the *agent* owns the real source review.
- **PR #14 hardening:** explicit issue-to-PR duplicate references, Git stdout/stderr capture budgets, bounded no-follow npm and policy-file reads, environment-isolated doctor tests, unresolved-profile classification, CI checkout cleanliness and fail-closed config documentation are integrated. These changes have exact-head hosted test coverage, not evidence of security against arbitrary hostile execution.
- **Remaining intentional limits:** large Git outputs fail closed rather than receive exhaustive treatment; work-item matching remains heuristic and comparison-budgeted; report privacy checking is advisory, not a redacted public export; private and uncommitted work is invisible to hosted-only review; identity must be explicitly supplied to the CLI when a specific repo is required.

### Runtime activation evidence — separate from this review

| Client | Available evidence | Honest disposition |
| --- | --- | --- |
| Antigravity CLI | Maintainer-supplied physical acceptance report: native discovery/invocation, helper and Full agent workflow, with 10 local Git fixtures | **Reported PASS** for native activation; not re-executed in this review |
| Claude Code | Maintainer directly confirmed `/freview full` works; prior Claude source audits and helper checks supplied separately | **Owner-confirmed native invocation and Full workflow**; model-selection and audit-depth caveats preserved |
| Codex CLI | Maintainer-supplied report: native `$freview` activation, helper smoke, bounded Full source review | **Reported PASS** for native activation; effective model independently unverified |
| OpenCode | Maintainer explicitly confirmed `/freview` works | **Owner-confirmed native slash invocation only**; helper execution and independent five-gate/full-audit acceptance not separately observed here |

Avoid asserting that any four agents were re-tested by this hosted review. Native activation can succeed even when its produced audit is appropriately labeled `partial-audit`.

## Historical reconciliation and duplicate work

Historical [draft PR #8](https://github.com/raiseCatError/freview/pull/8) is an authentic record of the earlier Antigravity experiment but its old base and descriptions must **not** be merged into the current mainline as though newly verified. The original manually followed skill instructions and did not establish native AGY activation in that session. The corrective implementation is already on `main` via PRs #9–#14. Close PR #8 **without merging** as superseded and preserve its branch and full record.

At this review baseline, GitHub returned **no standalone issues** and one open draft PR (#8). That PR is historical work, not an additional unmerged feature release. Thirteen older implementation/documentation branches remain in the remote alongside current `main` and the hygiene branch. Merged branch heads alone are not confirmed duplicate delivery and are **not** safe automatic deletion targets. No cleanup of branches, private worktrees or historical audit documents was performed.

## Findings and disposition

| ID | Severity | Finding or limitation | Evidence / proposed handling |
| --- | --- | --- | --- |
| R-01 | P3 | GitHub repository description is empty | GitHub repository metadata; optional manual settings update (connector has no repository-description write action) |
| R-02 | P3 | Native OpenCode Full acceptance beyond invocation is unobserved | User-confirmed slash invocation, but no independent helper/Full report from that client; record as limitation rather than claiming all five gates |
| R-03 | P3 | Human accessibility QA and deliberately opt-in security scanning remain unperformed | `docs/testing/agent-activation-acceptance.md` and `SECURITY.md`; not a reason to invent a passing test |
| R-04 | Information | Public report publication requires manual privacy review | `report_tools.py --check-public` is advisory and may miss sensitive data; never commit raw local machine reports |
| R-05 | Information | Historical PR #8 and old merged remote branches require historical handling, not source integration | Close PR #8 with a supersession note; leave branches intact absent specific disposal authorization |
| R-06 | Information | Version has not been released or tagged | Exact GitHub tags and Releases listings; maintain release hold at maintainer request |

**No new P0/P1 defect was confirmed within the bounded inspected scope.** This is not proof that all future defects are absent. No proposals here authorize implementation, release creation or deployment.

## Verification manifest and what was not done

- **Performed directly here:** GitHub repository/ref, open/merged PR, issue, branch, release and tag reads; source/CI/docs/fixture inspection; cross-check of previously supplied external agent reports. No repository or external agent environments were modified by the audit itself.
- **Previously performed by other systems:** exact-SHA [99-test Ubuntu/macOS run](https://github.com/raiseCatError/freview/actions/runs/38983887532), earlier physical Antigravity local fixtures, prior user-submitted Claude and Codex source reviews. Those are cited as external observations, **not rerun** by this reviewer.
- **Not observed:** user Mac's current uncommitted files, fresh OpenCode helper or Full workflow evidence, any live screen reader, local malicious-repository adversarial run, vendor-paid specialist review, full GitHub security-alert settings, and independent attestation of agent execution manifests.

## Pre-release handoff (pause point)

1. Verify this hygiene change on its **own exact PR head** under existing Ubuntu/macOS CI, then integrate only if successful.
2. Close [draft PR #8](https://github.com/raiseCatError/freview/pull/8) as superseded, leaving its original audit and branches intact.
3. Preserve status **pre-release, ready with limitations**. **Do not create tags, GitHub Releases, deployments or automatic schedulers.**
4. Maintainer may update the local checkout and installed skills manually after the merge; hosted GitHub edits do not update an existing Mac checkout or installed user skill copies.

**Publication gate remains intentionally closed at the owner's request.**
