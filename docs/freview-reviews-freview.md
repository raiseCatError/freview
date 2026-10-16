# freview reviews freview

*The auditor has become the audit target. Nobody is allowed to close the issue simply because the auditor says it's done.*

**Audit date:** 2026-10-17 (IST)  
**Repository:** [raiseCatError/freview](https://github.com/raiseCatError/freview)  
**Audited ref:** \`main\` at [\`9227430eca021d0076c0e9b888631facad528e3e\`](https://github.com/raiseCatError/freview/commit/9227430eca021d0076c0e9b888631facad528e3e)  
**Requested style:** Full, including an examination of the code and delivery evidence  
**Actual report classification:** **Partial audit** — live GitHub metadata, source inspection and CI receipts reviewed; the freview CLI itself and official external code reviewers were **not** executed in this environment.

> **Verdict:** A credible early-preview skill, not yet an independently validated all-agent, all-repository audit system. Zero confirmed duplicate tickets. One formerly confused installation guide. A suspicious number of opportunities for freview to audit itself again.

## 1. What freview found in the mirror

| Area | Evidence observed | Assessment |
| --- | --- | --- |
| Project identity | Portable Agent Skill, Python standard-library helpers, MIT license; [tree](https://github.com/raiseCatError/freview/tree/main) | Clear project and low runtime dependency burden |
| Main and history | \`main\` at the SHA above; [PR #1](https://github.com/raiseCatError/freview/pull/1), [#2](https://github.com/raiseCatError/freview/pull/2), [#3](https://github.com/raiseCatError/freview/pull/3) merged | Integrated; no evidence of an open PR at review time |
| Branch inventory | Four remote branches: \`main\`, \`feat/universal-agent-skill\`, \`fix/pre-v01-hardening\`, \`fix/pre-v01-final-audit\` | Three prior merged branch heads are potential *manual* archiving candidates, not deletion instructions |
| CI | [\`38960000430\`](https://github.com/raiseCatError/freview/actions/runs/38960000430): Ubuntu and macOS successful at the audited SHA; **52 tests per runner** | Automated checks verified for that exact revision |
| Community files | README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SUPPORT, SECURITY, ACCESSIBILITY | Good baseline; issue/PR templates optional but absent |
| Dependency graph | Helpers are Python standard-library based; no npm/Python dependency manifest at repository root | An empty GitHub Dependency graph would not itself be an error |
| Releases | No published GitHub Release returned | Correctly **not** claimed as a released v0.1.0 artifact |
| Open work | No open PRs or standalone issues returned at the audited moment | Small tracking surface, not proof of feature completeness |
| Genuine work-item duplicates | Three merged PRs address different phases: bootstrap, security hardening, final fixes | **None confirmed** in this limited metadata inventory |

*The branch and issue inventory is a snapshot. It is not a claim about private worktrees, unpushed changes, archived GitHub Projects, or future GitHub state.*

## 2. Findings — the uncomfortable part

### F-01 · P1 · Installation instructions still talked to Gemini CLI

**Evidence:** The README told users to run \`gemini skills install ...\`, despite Google's [May 2026 transition announcement](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/) and [Antigravity Agent Skills documentation](https://antigravity.google/docs/skills?tab=cli). For individual Free, Pro and Ultra accounts, Gemini CLI service ended June 18, 2026; older enterprise and supported API-key use is an exception.

**State:** **Documentation corrected in the PR accompanying this report**; not a defect in audited \`main\` until that PR merges.

**Repair plan:** Replace the outdated command with an explicit \`antigravity-cli\` installer target, document the current \`.agents/skills\` workspace and \`~/.gemini/antigravity-cli/skills\` global paths, and advise users to verify \`/skills\` in \`agy\`. Do not imply this has been physically smoke-tested.

**Verification:** Review the changed README, then install on an actual Antigravity CLI host and confirm \`/freview\` loads the installed \`SKILL.md\` and its referenced files. Also inspect the known [global installer path issue](https://github.com/vercel-labs/skills/issues/1851).

### F-02 · P1 · “Full” still depends on an agent to actually do the full review

**Evidence:** [\`SKILL.md\`](https://github.com/raiseCatError/freview/blob/main/skills/freview/SKILL.md) describes an agent-driven investigation; [\`review.py\`](https://github.com/raiseCatError/freview/blob/main/skills/freview/scripts/review.py) deliberately emits a \`local-snapshot\`. Its CLI does **not** collect all GitHub issues, PR reviews, code behavior or hosted release gates. The [JSON report validator](https://github.com/raiseCatError/freview/blob/main/skills/freview/scripts/report_tools.py) enforces presence and structure of evidence, not whether the reported evidence is true.

**State:** Intentional architecture, **not a missing feature secretly marked released**. Still an end-to-end acceptance gap for the advertised Full experience.

**Repair plan:** Run real Standard and Full prompts on a pinned test repository through the supported agents, with cases for failed CI, misleadingly closed issues, overlapping tasks and incomplete source integration. Verify the agent downgrades to \`partial-audit\` whenever required checks are unavailable. Record each agent/version and permissions. Do not add an elaborate service until the manual workflow succeeds.

**Verification:** Check the generated report's \`verification_manifest\`, \`duplicate_clusters\`, \`remediation_plan\`, exact SHA citations and unverified categories. Ensure no third-party scan, GitHub comment or paid review was invoked without approval.

### F-03 · P2 · Duplicate identification is intentionally conservative, not magical

**Evidence:** [\`duplicates.py\`](https://github.com/raiseCatError/freview/blob/main/skills/freview/scripts/duplicates.py) uses title tokens, explicit references and simple matching, capped at 3,000 exported records. It labels everything a **candidate** and does not download GitHub issues or inspect code clones.

**State:** Correctly documented limitation. The skill's agent instructions still require checking actual acceptance criteria and distinguishing a PR implementing an issue from a genuine duplicate work item.

**Repair plan:** For larger public projects, add a paginated, permission-aware metadata collector **after** real end-to-end tests; retain candidate-only classifications until a human/agent verifies identical deliverables. Introduce fixtures with parent/child, backport, similarly worded but different requirements, and distinct QA tasks.

**Verification:** No automatic closures; no duplicate-code analysis in the tracking module; clearly disclose truncated coverage.

### F-04 · P2 · Scheduled snapshot template is intentionally not plug-and-play

**Evidence:** [Daily template](https://github.com/raiseCatError/freview/blob/main/templates/github-actions/freview-daily.yml) invokes \`.freview/tools/repo_snapshot.py\`, but freview's distributed helper is inside \`skills/freview/scripts/\`. A consuming repository must deliberately vendor/pin that helper at the documented location before enabling the workflow. Uploading report artifacts is opt-in.

**State:** Installation step required, not evidence that unattended daily audits are running.

**Repair plan:** Document the vendoring step as a concrete prerequisite or supply a separately reviewed, version-pinned setup path. Keep the workflow disabled until explicitly copied/approved; don't auto-publish reports.

**Verification:** Test the template in a disposable repository, confirm the path exists, validate least-privilege permissions and inspect stored artifacts.

### F-05 · P2 · Portability and security claims need live-host acceptance

**Evidence:** [CI](https://github.com/raiseCatError/freview/blob/main/.github/workflows/checks.yml) covers Ubuntu and macOS on Python 3.11. The helper disables known Git fsmonitor/filter execution paths and inherited Git overrides; [SECURITY.md](https://github.com/raiseCatError/freview/blob/main/SECURITY.md) appropriately says this is **not an OS sandbox**.

**State:** Unit-tested on two runners; Windows, hostile OS environments, and actual Claude Code / Codex / OpenCode / Antigravity CLI skill discovery are not validated by that CI.

**Repair plan:** Prioritize an installation-and-invocation smoke matrix for those agents. Only add Windows CI if Windows is claimed as a supported target. Do not execute freview against untrusted repositories on a credential-bearing workstation without isolation.

**Verification:** Real \`/freview\` invocation, included references accessible, no unintended writes or network transmission, understandable failure when a checker cannot run.

### F-06 · P2 · Minor repository metadata and tracker polish

**Evidence:** GitHub's repository description was empty at review time; issue and PR templates were absent, although contribution and security documents exist. Three merged feature/hardening branches still appear in remote branch listings.

**Repair plan:** Add a short description and lightweight public issue/PR templates if useful for contributors. Review historical branches with the owner before proposing archive/delete actions; they're part of the project's development history.

**Verification:** GitHub community page and branch ancestry review, **no automatic cleanup**.

## 3. Remediation sequence (none executed by the audit)

| Priority | Proposal | Owner / dependency | Acceptance gate |
| --- | --- | --- | --- |
| P1 | Correct the Antigravity install docs | Documentation PR (this report) | Confirm current Google docs + one actual \`agy\` smoke test |
| P1 | End-to-end test Standard and Full on a fixture repository | Maintainer / available installed agents | Valid evidence manifest, accurate missing/failed statuses, no hidden mutations |
| P2 | Add optional larger-scale metadata collection | Later, only if small-repo workflows prove valuable | Accurate pagination, no false duplicate confirmation |
| P2 | Test daily template in a disposable consumer | Maintainer; pin/version helper | Working path, restricted permissions, no automatic uploads |
| P2 | Consider README/GitHub community polish | Maintainer | Contribution workflow is clearer, no unnecessary files |

### What was *not* done

The available runtime **could not clone GitHub over the container network**, so I followed freview's documented procedure through the connected GitHub API and source inspection. I did **not** run \`python3 .../review.py\` from a freview checkout, invoke the official Claude/Codex code-review systems, inspect private/unpushed worktrees, run external vulnerability scanners, verify branch protections, or perform real Antigravity/Claude/Codex/OpenCode installation tests. This is a **partial agent-assisted dogfood audit**, not a \`full-audit\` receipt.

The 52 tests-per-platform result is an **existing GitHub CI receipt**, not tests rerun by this review. Reports cannot prove the truth of arbitrary citations simply by validating JSON structure.

---

## 4. Recursive conclusion

**freview can review freview, but freview must not approve freview just because freview says freview looks fine.**

It has real automated coverage, a coherent read-only design, good community documentation and an explicit distinction between implemented, verified and released. The immediate documentation mismatch is addressed in the accompanying PR. The most meaningful next test is still a **real installed-agent end-to-end review**, not another decorative feature or automatic fixer.

*Recursion depth: 1 · Confirmed duplicate work items: 0 · Unverified claims kept unverified: as intended.*
