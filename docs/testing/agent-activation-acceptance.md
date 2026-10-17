# Physical freview agent-activation and self-review acceptance

**Purpose:** Verify that the *Agent Skill itself* is discovered and activated, separately from successful Python helper execution. This checklist requires a real local agent session. It cannot be completed through GitHub CI alone.

**Latest evidence (2026-10-17):** See the [final pre-release source review and owner-reported native runtime results](../audits/2026-10-17-final-pre-release-self-review.md). This page is the *acceptance protocol*, not a claim that its five checks have been executed for every client. The user reports native `/freview` invocation in OpenCode; a separate physical OpenCode Full report was not provided for this record.

## Baseline and permissions

Before testing, record: target repository identity, current directory and Git root (if any), selected ref/HEAD, whether working tree is dirty, installed freview skill path and asset hash/ref, agent binary/version, chosen model and reasoning setting, timezone, expected scratch volume and permissions.

- Use a **fresh session**; don't reuse a conversation whose system prompt cached old skill definitions.
- Run on a reviewed, verified scratch volume appropriate to the host. If the user has a specific external-storage policy, check actual mount and capacity before any output. Never silently fall back to the internal disk.
- Test by reading source and metadata; **no edits to an existing project**, installs, package manager scripts, Git fetch/checkouts/merges, commits, pushes, automated issue/PR changes, tags, releases or deployment.
- Never run unreviewed project scripts, optional third-party code reviewers or security scanners merely to get a PASS.
- Use short, bounded operations; record commands, exit codes and platform versions. If a gate needs human action, mark pending rather than guessing.

## Five independent activation checks

| Gate | What proves it | Wrong substitute |
| --- | --- | --- |
| 1. Installed package | Explicit physical path with full bundled references/helpers and a source fingerprint | A folder named `freview` alone |
| 2. Native discovery | Native skill listing in the invoking client after startup/reload | Python can read SKILL.md |
| 3. Native invocation | Explicit skill command/UI invocation recognized by the client; session evidence | Agent manually reading SKILL.md after a user asks |
| 4. Helper execution | `python3 -I` quick/standard/full snapshots execute and mark themselves `local-snapshot` | A script exiting zero means complete AI review |
| 5. Actual Full review | Agent traces relevant implementation + tests + exact-head CI + human gates, gives cited findings and honest `partial-audit` when gaps exist | JSON schema-valid report without source evidence |

Record **PASS**, **FAIL**, **PARTIAL** or **NOT OBSERVED** per gate. Do not relabel manual skill-following as native activation. For failed AGY discovery, compare `{workspace}/.agents/skills/`, `~/.gemini/antigravity-cli/skills/`, and `~/.gemini/config/skills/`; confirm whether a symlink is respected and whether restart/reload is necessary. Document observations, do not invent global path guarantees.

## Local versus cloud test cases

On a verified **disposable Git fixture**, not a live NMSh checkout, sample these states:

| Local evidence | Expected classification |
| --- | --- |
| `git init`, a file exists, no initial commit | Unborn HEAD; staged/untracked state present; no remote publication claim |
| Initial commit, then a new untracked source file | `untracked` and not included in HEAD-based reachability claims |
| Tracked file staged, then edited again | One path appears in both `staged` and `unstaged`; Full agent considers two distinct diff layers |
| Clean Git checkout with local commit ahead of cached upstream | Candidate local-ahead; remote publication remains **unverified**, not provably unpushed |
| Local commit with no tracking upstream | No upstream configured; does not prove an absent push |
| Two linked worktrees, second dirty | Enumerate both; inspect sibling status only after explicit user opt-in, bounded, read-only |
| Wrong repository directory | Require target identity match or stop for clarification |
| Cloud-only GitHub access | Local staged, unstaged, untracked, worktrees and unpushed commits all `not observable` |
| Visible files but no Git repository | Explicit non-Git source review; Git helper N/A and no implicit `git init` |

Never infer the intended development base solely from `origin/HEAD` or `origin/master`; distinguish chosen integration, development and publication targets.

## Private evidence, report safety and provenance

- Build an execution manifest: command + cwd + SHA + exit status + version + UTC + source of observation. Distinguish self-reported prior evidence from agent-executed tests and hosted CI receipts.
- Keep original reports on user-approved local storage. `report_tools.py --check-public` is **advisory**, not a guarantee; its exit 0 still requires manual privacy review. Do not publish branch names, local paths, secret patterns, private titles, prompt contents, or uncommitted source to public GitHub.
- Compare the actual current freview HEAD to [historical PR #8](https://github.com/raiseCatError/freview/pull/8), including verified changes and unexplained regressions, without editing the historical audit. Preserve UTC accuracy.
- Use `full-audit` only if all selected applicable categories were actually checked and evidence supports it; otherwise `partial-audit`. A successful source inspection does not establish physical VoiceOver or terminal/device QA.

## Final reporting template

Record a compact matrix of five activation gates, source paths/SHAs, operating system/agent/model, local/cloud test-state results, per-category verification manifest, observed defects and reproduction steps, skipped checks, and an explicit **release-readiness verdict**. Do not push or merge the report unless the owner separately authorizes publication and the content has passed privacy review.

A new feature request, repair suggestion or approved follow-up is separate from the read-only acceptance run.
