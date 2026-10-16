# Git history, branches, worktrees and integration

This is **history hygiene**, not a demand for linear Git history. A healthy project can intentionally use merge commits, parallel release branches, cherry-picks and preserved worktrees.

## Local read-only inventory

- `git status --porcelain=v2 --branch` — dirty/unknown local state. Don't discard it.
- `git worktree list --porcelain` — shared branch ownership, detached worktrees and locks. Never prune as part of an audit.
- `git for-each-ref --format='%(refname:short) %(objectname) %(upstream:short) %(upstream:track)'` — local branches, upstreams and tracking gaps.
- `git log --graph --decorate --oneline -n 80 --all` — bounded visual sample only, not complete ancestry proof.
- `git merge-base --is-ancestor A B` — ancestor relation; exit 1 means no ancestry, *not* absence of equivalent cherry-picked changes.
- `git rev-list --left-right --count A...B` — divergence; review chosen branch roles before concluding “behind”.
- `git diff --check A...B`, `git diff --name-status A...B` — targeted branch change checks.
- `git ls-files` plus safe inspection for accidental generated artifacts; no `git clean`, `git gc`, `git branch -d` or deleting directories.

If the repo is shallow or remote refs stale, stop short of exact-ancestry claims or explicitly state that `git fetch` was **not** authorized. Ask before fetching if correctness materially requires fresh objects and no read-only online route is available. Do not automatically invoke `git fetch --prune`.

## PR and branch integrity

For each critical PR: record base/head SHA, fork/source, draft state, mergeability, review conversations, changed paths, conflicts, check-run summary and exact accepted head. Classify whether:
- actually merged/reachable on integration ref;
- implemented only on isolated feature branch;
- included in an unreleased integration/release candidate;
- superseded by a later reimplementation;
- equivalent via squash/cherry-pick, requiring patch-id/tree inspection;
- still in a live worktree; or
- ambiguous because Git history, permissions or local data are missing.

Locate overlap hot spots across concurrently active branches; recommend ownership and a safe integration order, **without attempting the merge**. A remote PR marked merged proves a GitHub event, not automatically published code. A locally clean branch doesn't mean remote CI passed. Avoid flagging long-lived release branches as stale merely by age.

## Network graph

GitHub's Network graph visualizes branch/fork history. It is not the dependency graph and doesn't show completeness or automatically prove which source-tree features are shipped. Use it for orientation, then verify relationships with SHAs and merge-base/history data.
