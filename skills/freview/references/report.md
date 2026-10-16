# Review report contract

Always include:
- Repository, root/remote, observation timestamp, *exact* base/head SHAs, development and publication branches, selected/excluded categories, audit mode, available local/remote permissions.
- Short executive summary with critical blockers, meaningful discrepancies and factual limitations.
- Status classification separate from priority/severity.
- Evidence-linked findings, including affected criterion or project requirement, source path/commit, relevant test/CI (exact SHA and jobs), human QA and actual release reachability.
- Git history and integration: branch/worktree collisions, divergence, wrong PR bases, candidate chains, coverage limits, conflicts and duplicates; explicitly state when local branches are **not observable**.
- Repository hygiene: project-dependent community, docs, security, dependency and accessibility findings (only selected/applicable areas).
- A separate **actionable remediation plan for every confirmed actionable problem**, giving ordered repair steps, owner/dependencies, risks, effort uncertainty and concrete CI/QA validation. Plans never perform edits.
- **Duplicate clusters** for issues, PRs, roadmap milestones, trackers and duplicate delivery efforts with confirmed vs suspected status and evidence; never code clones.
- Implementation designs for never-started/new features **only when the user opts in** using `--suggest-implementation`.
- A small prioritized list of *non-destructive* next actions; no assumption user approves fixes.
- An explicit **Not checked / Not observable** table or paragraph.

## Verification manifest (required for agent audits)

A `partial-audit` or `full-audit` JSON report requires `verification_manifest` entries for **each selected category**. Every entry states `category`, `status` (`verified`, `partial`, `not-observed`, or `not-applicable`), evidence/source links and, when applicable, exact ref and tool/version. `verified` means the promised *review/check was actually performed*, not that the project has no defects. `not-applicable` requires an explanation.

A `full-audit` may use that label only if all selected categories were reviewed or genuinely inapplicable, with code review actually evidenced when selected. Otherwise issue a `partial-audit` and explicitly record omissions. Never claim Full simply because an agent was instructed to perform it or a local metadata helper succeeded.

## Severity ≠ status

Priority P0/P1/P2 describes urgency/impact. Status describes actual lifecycle stage: research, isolated, integrated candidate, verified, human accepted, shipped, deferred, unknown. An intentionally unimplemented feature is not automatically a P0 defect; a false “released and safe” claim can be.

## Evidence hierarchy

Prefer directly observed code and Git metadata, forge API and CI receipts, signed/published artifacts, and physical reports with exact environment over stale docs, unchecked boxes or agent claims. A fresh report should cite accessible issue/PR/commit links. Do not manufacture line numbers or GitHub refs. Label proposed interpretations as tentative.

## Output table

| Priority | Area | Claim / expected behavior | Observed evidence | Actual state | Next smallest action |
| --- | --- | --- | --- | --- | --- |
| P1 | issue #... | available in released build | only isolated PR SHA, no release reachability | implemented isolated | integrate/test later |

For large inventories, organize by area; provide counts **only for the enumerated scope** and say if pagination, permissions or recent changes mean the count may be partial. Avoid copying large private issue/CI contents or full files into reports.

## Remediation and duplicate classification

Follow [repair-plan rules](remediation.md) and [duplicate evidence rules](duplicates.md). The machine-readable agent report must include `remediation_plan` and `duplicate_clusters` for partial/full audits. Each confirmed actionable finding needs a repair plan or an explicit reason why it is blocked. Standard cannot invent exact code changes without source access; Full can use code reviewer evidence. Duplicate issue/PR/workflow candidates never auto-close.

## Completion wording

Never say “repository is completely clean” from incomplete evidence. Say “No findings in the selected scope as of SHA X; excluded/unobservable categories Y.” Do not auto-open tickets or fix anything.

## Versioned JSON and daily deltas

The portable [report.schema.json](../assets/schemas/freview-report.schema.json) defines report envelope, exact SHA/source scope, category coverage, evidence-linked findings, severity separate from lifecycle status, and explicit unobserved facts. Agent-generated reports must distinguish `report_kind=full-audit`, `partial-audit` and `local-snapshot`. The companion helper always emits `local-snapshot`; only the actual agent investigation can justify a wider audit.

Use `python3 <installed-skill>/scripts/review.py --mode standard --format json` to generate a local snapshot to stdout. Pass an explicit `--output /approved/scratch/report.json` to write one new report file; the command never overwrites existing files or creates directories.

Use `python3 <installed-skill>/scripts/report_tools.py REPORT.json` to validate the supported common report fields, and `python3 <installed-skill>/scripts/report_tools.py PRIOR.json CURRENT.json` to compare new/resolved/changed finding IDs. Add `--format json` for machine-readable delta. This standard-library validator is deliberately a limited structural validator, not a complete JSON Schema validator; downstream consumers may enforce the complete published schema separately.

Only compare reports with matching repository identity, report kind and category coverage. A disappearing finding is a candidate for revalidation, not proof of remediation if investigation coverage differs. Without a supplied prior report, never pretend a previous daily run occurred.

Do not automatically publish a local report to GitHub or include sensitive path/history content in public artifacts. The latest report always names excluded categories and unobserved evidence.
