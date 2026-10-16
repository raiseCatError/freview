# Modes, configuration and scope selection

## Modes

| Mode | Purpose | Enumeration | Depth |
|---|---|---|---|
| quick | 1-minute-style orientation; major red flags | small bounded sample, always state limits | metadata and obvious conflicts |
| standard (default) | credible release/repository health | relevant open issues, PRs and recent closed samples | critical paths and exact-SHA examples |
| full | comprehensive evidence review | paginate all accessible scoped records | trace material acceptance and CI, never unbounded execution |
| targeted | selected categories/refs/issues | only requested scope | enough to substantiate claim |

“Full” covers all **applicable structural checks**: git, tracking, implementation, CI, releases, docs, community, dependencies, security-posture, accessibility. It **includes** deep code review by default, preferring an installed trusted specialist and otherwise a bounded native code review. It never automatically installs a skill/tool, runs high-risk scans or uploads source. External vulnerability/security scans still require `--with security-scan`, and exclusions take precedence over mode defaults. In quick, report partial remote coverage rather than describing a truncated result as the total backlog.

Category aliases in natural language: `git` includes worktrees and ancestry; `tracking` includes issues, milestones and PRs; `implementation` traces feature reachability and tests; `docs` checks release and help accuracy; `community` includes contributor/onboarding standards; `dependencies` includes manifests, lockfiles and dependency graph; `security-posture` is documentary/configuration evidence, not a vulnerability verdict.

## Conversational interface

- Bare `freview`: run **standard**, the recommended daily review, without an extra question when the repository is identifiable. Ask one concise question only if essential inputs are genuinely missing. Deep code review is off in standard, on in full; external security scanning is off unless explicitly included.
- `freview full excluding ci and code review` → full without those categories. Exclude always wins over default inclusion.
- `freview only git, releases` → targeted; do not scan other areas just to fill a report.
- `freview full` → include deep code-quality review, using a trusted installed specialist if available; fall back to a native code review if no usable specialist exists. `freview standard --with code-review` also enables it.
- `freview quick --base origin/develop` → use the specified ref if it exists; otherwise report inability, don't quietly substitute a different branch.
- `freview full on repo owner/repo` → remote-only if no local files; do not pretend to have local worktrees.

## How to adapt

Infer, do not hardcode:
- Project kind: app/library/CLI/mobile/firmware/service/web/monorepo/content/docs/data/infrastructure/archived.
- Forge: GitHub/GitLab/other/local-only; auth permission and pagination limitations.
- Branch policy: main/master/dev/develop/trunk/release trains; user-chosen base wins.
- Release: tags, packages, images, artifacts, marketplaces, app stores, deployment receipts; a tag is not always deployment.
- CI: actual enforced jobs and skips across versions, platforms, release gates; N/A for projects without CI.
- Language/package: use manifest/lockfile rules appropriate to each ecosystem; avoid treating all lockfiles as mandatory.
- Risk: local hardware, production safety, secrets and regulated data.

Optionally read and validate root `.freview.json` using [project config](configuration.md) and [versioned schema](../../../schemas/freview-config.schema.json); never execute arbitrary config commands or create files automatically. The repository's existing documentation is first-class evidence, with conflicts recorded instead of silently resolved.

## Budget

Bound scope to the selected mode. Prefer reusable already-available verification receipts. Do not rerun tests that have trustworthy exact-SHA evidence merely to inflate work. If a full pass is infeasible, make explicit the exact pages, branches, files and CI runs not covered and offer a follow-up narrower pass without asserting completion.
