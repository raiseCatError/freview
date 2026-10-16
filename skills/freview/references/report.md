# Review report contract

Always include:
- Repository, root/remote, observation timestamp, *exact* base/head SHAs, development and publication branches, selected/excluded categories, audit mode, available local/remote permissions.
- Short executive summary with critical blockers, meaningful discrepancies and factual limitations.
- Status classification separate from priority/severity.
- Evidence-linked findings, including affected criterion or project requirement, source path/commit, relevant test/CI (exact SHA and jobs), human QA and actual release reachability.
- Git history and integration: branch/worktree collisions, divergence, wrong PR bases, candidate chains, coverage limits, conflicts and duplicates; explicitly state when local branches are **not observable**.
- Repository hygiene: project-dependent community, docs, security, dependency and accessibility findings (only selected/applicable areas).
- A small prioritized list of *non-destructive* next actions; no assumption user approves fixes.
- An explicit **Not checked / Not observable** table or paragraph.

## Severity ≠ status

Priority P0/P1/P2 describes urgency/impact. Status describes actual lifecycle stage: research, isolated, integrated candidate, verified, human accepted, shipped, deferred, unknown. An intentionally unimplemented feature is not automatically a P0 defect; a false “released and safe” claim can be.

## Evidence hierarchy

Prefer directly observed code and Git metadata, forge API and CI receipts, signed/published artifacts, and physical reports with exact environment over stale docs, unchecked boxes or agent claims. A fresh report should cite accessible issue/PR/commit links. Do not manufacture line numbers or GitHub refs. Label proposed interpretations as tentative.

## Output table

| Priority | Area | Claim / expected behavior | Observed evidence | Actual state | Next smallest action |
| --- | --- | --- | --- | --- | --- |
| P1 | issue #... | available in released build | only isolated PR SHA, no release reachability | implemented isolated | integrate/test later |

For large inventories, organize by area; provide counts **only for the enumerated scope** and say if pagination, permissions or recent changes mean the count may be partial. Avoid copying large private issue/CI contents or full files into reports.

## Completion wording

Never say “repository is completely clean” from incomplete evidence. Say “No findings in the selected scope as of SHA X; excluded/unobservable categories Y.” Do not auto-open tickets or fix anything.
