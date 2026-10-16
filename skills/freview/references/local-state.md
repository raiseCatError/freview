# Local-first and cloud-only repository evidence

A GitHub PR, a local Git commit, a staged diff, an unstaged working-tree edit and an untracked file are **different evidence layers**. A missing remote PR or green CI on another SHA is not proof a feature is unimplemented locally.

## Decision: where is the source of truth?

Before collecting evidence, identify the **user's target repository**, which may differ from the current working directory.

- **Local checkout available, target identity matched:** run the bounded local snapshot and inspect requested changes. Match canonical forge identity where available; otherwise compare the Git common directory, worktree relationships and explicit user input. If uncertain, ask before auditing the current directory.
- **Cloud-only access (GitHub/GitLab/Codeberg/etc.):** review hosted branches, PRs, files, CI, releases and policies via authorized APIs. State: **uncommitted files, untracked files, unpushed commits and local worktrees are not observable**. Do not run local helpers or pretend they prove absence.
- **Local directory with `git init` but no commits:** use Git status to inspect staged and untracked work, record `HEAD=null` and an unborn branch. Avoid graph calculations or publication assertions.
- **Local source with no Git at all:** the Git snapshot helper is not applicable. Review bounded visible files with ordinary read-only filesystem inspection if permitted, mark Git history/remote linkage as unobserved, and never initialize a repository automatically.
- **Multiple unrelated repositories/workspaces:** track a separate identity, ref and coverage card per repository. Never combine results based only on a matching folder name.

## Local state review order

1. Discover `git rev-parse --show-toplevel`, `git rev-parse --git-common-dir`, current branch/HEAD, configured remotes and tracking upstream. Safely compare repository identity to the requested project; explicitly detect a mismatch.
2. Inventory **staged changes** (index vs HEAD), **unstaged changes** (working tree vs index), and **untracked** paths separately. `repo_snapshot.py` reports bounded path metadata under `local_changes`; it does **not** inspect source content.
3. In **Full** mode, review **actual staged diff bodies and unstaged diff bodies separately** using safe, bounded, non-executing Git inspection. Also inspect relevant untracked source files within granted scope; Git diffs cannot show untracked contents. Avoid secrets, huge binaries, generated files, ignored trees and arbitrary repository scripts. A file can have both staged and unstaged modifications.
4. Check **local commits relative to the intended integration base** and separately against the **configured cached upstream**. `publishing.ahead` is a tentative local-vs-cached-ref signal, **not proof the commit is unpublished**, because caches can be stale and other remotes can contain it. A branch without upstream is not necessarily unpublished.
5. Obtain **authoritative forge evidence** for publication and exact-commit CI where network access and permission permit. Label unsynchronized evidence rather than inventing a push or claiming the remote contains local changes.
6. Enumerate worktrees and common-Git-dir identity. **Do not scan other worktree contents by default**; use `--scan-worktrees` only with explicit opt-in and bounded budget. Active concurrent agents may change other worktrees while an audit is running.
7. Track implementation status by evidence source: **local-untracked**, **local-unstaged**, **local-staged**, **committed-local**, **remote-ref-confirmed**, **PR-candidate**, **integrated**, **CI-verified-exact-SHA**, **human-verified**, **released**. Do not compress these into a single binary “done”.
8. Preserve **observed SHA, dirty status, local snapshot timestamp, inspected files and unverified limits**. Uncommitted work has no commit SHA; never attribute working-tree source to HEAD alone.

## Helper examples

From the *actual* requested Git checkout, no writes by default:

```sh
python3 -I <installed-freview>/scripts/repo_snapshot.py --json --max-divergences 40
python3 -I <installed-freview>/scripts/review.py --mode full --format json --max-divergences 40
```

To **opt in** to status checks of other local worktrees (not a diff audit):

```sh
python3 -I <installed-freview>/scripts/repo_snapshot.py --json --scan-worktrees --max-worktrees 8
```

To fail closed on a mistaken local directory when its canonical identity is known:

```sh
python3 -I <installed-freview>/scripts/review.py --mode standard --format json \
  --expect-identity forge:github.com/raisecaterror/freview
```

Use `--base` to explicitly select an integration branch when known. The helper's fallback to cached `origin/HEAD` is only a comparison reference, not a determination of the actual development/release base. Agent review should separately document credible alternative bases and ask if ambiguous.

## Threat/privacy boundaries

- Local paths, branch names, untracked file names, diff contents and commit messages can contain private information. **Never upload or publish these automatically**.
- No source execution, installs, arbitrary Git hooks or external diff programs. `python3 -I` is only Python import isolation, **not an operating-system sandbox**.
- `local_changes` is a **bounded metadata inventory**, not evidence of feature correctness or full local coverage. Ignored files and source content require separate authorized inspection.
- When a worktree is concurrently changing, observations are point-in-time snapshots and may not be transactionally consistent. Never fix or discard work without separate explicit permission.
