# Duplicate deliverables and tracking: evidence-first reconciliation

freview checks for genuinely duplicated **work items and deliverables**. It does NOT detect duplicated code, copied functions/classes or source clones: leave those to the selected official code reviewer in Full mode.

## Scope

- Issues: multiple open or closed issues requesting the same deliverable and overlapping acceptance criteria, including explicit `duplicate of #N` references.
- Pull requests: overlapping purpose, matching scopes/acceptance and parallel implementations attempting to deliver the same thing, including PRs targeting different release branches.
- Issue ↔ PR: detect wrongly separate records that represent identical change requests, without treating a normal PR implementing an issue as a duplicate.
- Milestones, GitHub Project cards, roadmap and release-train trackers: record mirrored entries that have diverged in state/owner or require consolidation.
- Documentation and generated checklists: repeated or contradictory tracking requirements; distinguish an intentional summary/index link from an accidental duplicate specification.
- Git branches/worktrees: independently implemented *same deliverable* and incompatible overlapping acceptance; do not call two branches duplicates just because they edit the same files.

## Identification

Gather candidates using normalized titles and aliases, explicit `duplicate` links, linked issues/PRs, cross-references, descriptions, acceptance items, key nouns/action/target versions, and common files/configuration areas **as metadata**. In Standard, do NOT read source implementation code. In Full, source-level wiring evidence may clarify deliverable duplication, not source-code cloning.

For a suspected pair establish:
1. Same intended user-facing outcome, target scope and acceptance criteria? Link the exact text/issue/PR.
2. Same affected subsystem and release requirement? Different environments, versions, policies, or follow-up stages can make both issues valid.
3. Evidence that one deliverable would satisfy *both* without losing a distinct requirement? A PR implementing an issue is *not* a duplicate; neither is parent/child, dependency, research/design vs implementation, regression vs future enhancement, backport or distinct QA tracker.
4. Explicit existing duplicate linkage or confirmed identical deliverable with authoritative issue history? Only then classify **confirmed duplicate**. Otherwise **candidate / related / intentional parallel** with confidence and explanation.

Do not deduplicate purely by title similarity, shared keywords, common changed files, common assignee, repetitive descriptions or a search rank. Never silently close/relabel issues, delete branches, consolidate PRs or modify trackers.

## Output

For each suspected/confirmed cluster show: canonical recommended work item (with rationale, not a destructive action), other issue/PR/roadmap references, status (confirmed/candidate/related/not duplicate), exact evidence and non-matching acceptance constraints, confidence, reason and proposed non-destructive consolidation/check step. If status confirmed, explain how to preserve links, comments, acceptance conditions, ownership and historical evidence before any future close/merge.

[Optional local metadata helper](../scripts/duplicates.py) accepts explicitly exported issue/PR metadata and returns **candidates only**. It never fetches, accesses source code, or auto-confirms duplicates.


## Non-closing references, stdin and comparison budgets

The metadata checker recognizes PR/issue relationships via `Closes #N`, `Fixes #N`, `Resolves #N`, and non-closing `Refs #N`/`References #N`. Non-closing links do **not** establish actual implementation, approval or release; compare the goals and delivery artifacts separately. This is particularly important when issues remain open until physical QA.

Input `-` reads bounded JSON from standard input (16 MiB max). `--max-comparisons` bounds candidate-search CPU work; `--max-pairs` bounds displayed candidates. Either budget can limit coverage: **zero candidates with truncated comparison coverage is not proof of zero duplicates**. No scanner executes issue instructions or closes anything. Prefer checked, attributable metadata feeds over blindly trusting current titles.
