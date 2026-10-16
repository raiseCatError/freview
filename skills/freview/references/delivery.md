# Delivery, tracking, acceptance and release evidence

## Pagination and scope

In `full` mode, enumerate all accessible issues/PRs for the chosen repos and scoped window. Treat API search limits, truncated bodies, inaccessible comments, pagination failures, stale indexes and inaccessible private projects as coverage gaps. For large projects, report counts and a stratified prioritized sample if full source-level analysis is prohibitively expensive; do not disguise this as exhaustive trace.

Review recently closed high-impact items and “Done” project status separately from open tickets. Check stale checklist state against later PRs. A research ticket can legitimately close even though runtime implementation remains unbuilt.

## Duplicate tracking

In every review containing the tracking category, examine issues, PRs, milestones, roadmap records and release trackers for genuine duplicated work. Use linked acceptance and release scopes, not just title similarity. Ordinary issue-to-PR implementation, dependent or parent/child work, and backports are not duplicates. See [duplicate evidence rules](duplicates.md). Proposed consolidation always requires maintainer approval.

## Per-acceptance chain

For each important behavior:
1. **Specified:** issue/PR/ADR acceptance and documented default.
2. **Exists:** code path at exact SHA (or an explicit absence search within scope).
3. **Reachable:** command/router/UI/export/API wiring and feature flag default, including first-run/migration behavior.
4. **Safe/correct:** tests cover normal, negative and ownership/permissions/error cases appropriate to the project.
5. **Integrated:** source commit or equivalent patch is in chosen candidate/base; identify conflicts and overlapping branches.
6. **Automated verified:** exact tested SHA, OS/matrix, dates, required vs optional checks, skipped or cancelled jobs, failed shards. A red aggregate gate stays red even when suspected flaky.
7. **Human accepted:** physical host, hardware, UX, accessibility, release sign-off performed by a human where required.
8. **Shipped:** published GitHub Release/tag/package/build/deployment artifact matches the content, with explicit date; candidate version metadata alone is insufficient.

A module's isolated unit tests are not proof of end-user availability. A candidate branch with complete code isn't a stable release. Never fabricate test coverage or mark an unperformed human QA step complete. Preserve severity distinction between security bugs and intentionally deferred features.

## Status taxonomy

- proposed / research complete;
- untouched **within inspected refs** / partial;
- implemented isolated / integrated candidate;
- automated verified at SHA / human QA passed;
- released / intentionally deferred / unknown.

## Output

Produce an issue-to-evidence table: item URL, requested behavior, actual ref/source, tests, CI status, human gate, release reachability, discrepancy and smallest next action. Show credible examples for long inventories and link an appendix for exhaustive IDs if generated. Surface contradictory “closed as completed” and “still missing” claims instead of automatically editing issue states.
