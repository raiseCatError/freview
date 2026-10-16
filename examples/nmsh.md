# Example: reviewing notMyShell (NMSh)

This is an example **consumer workflow**, not a rule baked into freview. freview discovers the current source of truth on every run, so the version, release branches and status shown in historical reports must never be hardcoded as live facts.

## Example invocation

```text
Use freview full on raiseCatError/notMyShell.
Exclude deep code-review and external security scans.
Discover branch conventions, releases, active issues/PRs, agent worktrees, candidate integrations and exact-head CI first.
Reconcile implementation with source and tests, especially any feature described as Done.
Treat physical Ghostty/Terminal.app QA, input ownership, privacy/security acceptance and release approval as human gates.
Do not edit, merge, delete, prune, fetch, install, clean or run full tests.
```

## What is repository-specific?

NMSh's own `AGENTS.md`, `CONTRIBUTING.md`, `ROADMAP.md`, release-train ledgers and issue descriptions determine the relevant policies. Its shell/PT Y, keyboard, clipboard and cross-shell behavior are not universal freview invariants.

If reviewing this repo remotely, say when no local worktree can be inspected. If an agent report cites a local SHA with no remote access, label it “reported, not independently verified”. A red CI aggregate stays red even if suspected flaky. A release candidate PR is not the published GitHub release.

## How projects customize

Document project-specific acceptance criteria in the project's existing contributor/agent/release policies. Invoke freview with a mode and exclusions; do **not** fork the generic SKILL.md for every project. Use a pinned installed copy of the skill if reproducibility matters, and update it deliberately.
