# Every report needs an actionable repair plan, not automatic fixes

freview produces both **findings** and **how-to-fix plans**. These plans guide maintainers; they are not permission to edit code or GitHub.

For each confirmed defect, stale closure, conflicting PR, missing CI/QA gate, outdated documentation, dependency mismatch, dangerous branch pattern or confirmed duplicate, provide:

- **Impact and priority** with user-visible or release consequence; distinguish blockers from deferred ideas.
- **Evidence and verification status:** exact issue/PR/commit/CI links; what is confirmed, inferred, unavailable and why.
- **Root cause or missing prerequisite**, or label unknown where evidence is insufficient. Do not guess.
- **Repair strategy**: smallest safe set of concrete actions, required owner/worktree/branch, order and dependencies; don't propose unnecessary rewrites.
- **How to validate**: exact relevant tests, CI matrix, user acceptance/physical QA, rollback/abort criteria; no unperformed test may be checked off.
- **Effort/risk** estimates only as qualitative bands with explicit uncertainty.
- **No mutation**: never fix, merge, close, prune, install, authorize, publish, post review comments or change protected refs during the audit.

For a **never-implemented feature** that is a new product request or explicitly deferred roadmap idea, the default should report its status and its smallest tracking/decision action, **not invent a design, estimate code changes or treat it as a defect**. Only on `--suggest-implementation` or a clear user request should freview add architecture, technical implementation options, tests and a proposed milestone plan for those future features. This opt-in does not authorize implementation itself.

Duplicate repair plans are conservative: verify the intended canonical record with maintainers, preserve unique requirements, cross-link PRs and historic discussions, and recommend closure/relabeling **for approval**, never apply it.

The standard daily review can recommend tracker/CI/documentation actions and note unverified source correctness; it cannot prescribe exact code-line fixes without source evidence. Full can propose code-level repairs based on reviewed files and specialist findings. Reports should end with a dependency-ordered consolidated plan (P0/P1/P2) and blockers, not just a list of findings.
