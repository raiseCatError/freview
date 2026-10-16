# freview

**Full Review**, pronounced **“f-review”** (the letter **F**, then *review*). Not “free-view” or “fre-view”.

**Full repository review, without guessing what “done” means.**

freview is a portable, evidence-first [Agent Skill](https://agentskills.io/) for assessing the *actual state* of a repository. It discovers how the project works before examining its Git history, worktrees, issues/PRs, implementation reachability, exact-commit CI, release process, documentation, community standards, dependencies and accessibility. It can optionally coordinate specialist code-quality and security reviews, **without copying their functionality**.

It produces a review, not a cleanup script. Default operations are **read-only**.

> **Status:** Initial portable skill. Installation and exact agent-discovery behavior may vary by agent version; verify it against your setup. The default audit is strictly read-only.

**Dogfooding:** [freview reviews freview](docs/freview-reviews-freview.md) — a self-audit that is intentionally less flattering than a green CI badge.

## Install

One portable skill: `skills/freview/SKILL.md`, with references and an optional Python-standard-library snapshot helper.

Recommended, using the [open `skills` installer](https://github.com/vercel-labs/skills):

```sh
# Install into your current project (choose supported agents when prompted)
npx skills add raiseCatError/freview --skill freview

# Or make it available across your projects
npx skills add raiseCatError/freview --skill freview -g
```

The `skills` installer supports Claude Code, Codex, OpenCode, **Antigravity CLI (`agy`)** and many other agents. It can create symlinks or copies depending on selected agent and platform; review permissions before installing. Run `npx skills add raiseCatError/freview --list` to inspect discovered skills without installing them. No official provider endorsement is implied.

For **Antigravity CLI (`agy`)**, select the current dedicated agent target:

```sh
npx skills add raiseCatError/freview --skill freview --agent antigravity-cli
```

Antigravity CLI discovers project skills in `.agents/skills/freview/` and global skills in `~/.gemini/antigravity-cli/skills/freview/`. In the `agy` TUI, use `/skills` to verify discovery, then `/freview` to invoke it. **Verify the actual installed path** when using `-g`: a reported installer issue has placed Antigravity CLI skills in the universal directory rather than its dedicated global directory. See [Google's Antigravity skills documentation](https://antigravity.google/docs/skills?tab=cli).

The older **Gemini CLI** was succeeded by Antigravity CLI for individual Free/Pro/Ultra accounts in June 2026; enterprise/API-key use of Gemini CLI continues. Do not use `gemini skills install` as the default setup path. See [Google's migration announcement](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/).

Codex's native skill installer can install a GitHub repo path; OpenCode discovers `.agents/skills/freview/`; Claude Code supports project and user skill directories. Use agent-specific installation only if your installed version supports the required path.

## Use

The examples below are **conversational skill instructions**, not commands supported verbatim by the Python helper. The Python helper is a separate local-metadata tool.

Ask your coding agent to invoke **freview** from inside a repository, or point it at a remotely accessible repository.

```text
freview                                  # Standard daily check; no code review
freview quick                            # Rapid factual snapshot
freview standard                         # Daily useful hygiene/status check
freview full                             # Complete status audit PLUS deep code review
freview full excluding security, docs    # Exclude selected categories
freview only git, issues, releases       # Target specific categories
freview standard --with code-review      # Add code review to a daily check
freview full --with security-scan         # Opt into an authorized specialist scan
freview full --base release/next         # Explicit candidate baseline
freview standard --suggest-implementation # Opt-in ideas for unimplemented features
freview only tracking,git --check-duplicates # Focused duplicate-work-item check
```

By default freview runs Standard, without unnecessary questions. It asks only when a missing essential detail or permission requires a decision. The default stays Standard unless you explicitly request another mode; project config cannot silently enable Full or external scans.

**Important:** Full includes a deep code-quality review, using a trusted installed specialist when appropriate or a bounded native review otherwise. Standard is the recommended daily check **without deep code review**. Full never silently installs tools, executes arbitrary scripts, runs expensive test suites, uploads private code, edits files or invokes external vulnerability scanners; those scanners remain opt-in.

## Review modes

| Capability | Quick | Standard (daily) | Full |
|:--|:--:|:--:|:--:|
| Identify project type, stack and policies | ✓ | ✓ | ✓ |
| Git branches, worktrees, ancestry and hygiene | Basic | ✓ | ✓ |
| Issues, PRs and stale completion claims | Basic | ✓ | ✓ |
| **Genuine duplicate tracking** across issues, PRs, plans and delivery initiatives | Candidates | ✓ | ✓ |
| CI and release readiness | Basic | ✓ | ✓ |
| Docs, community, dependencies and accessibility | Basic | ✓ | ✓ |
| Read implementation code and trace feature wiring | — | — | ✓ |
| Deep code-quality review | — | — | ✓ |
| Evidence-backed findings **and remediation plans** | ✓ | ✓ | ✓ |
| Optional suggestions for never-implemented features | Opt-in | Opt-in | Opt-in |
| External vulnerability scanners | Opt-in | Opt-in | Opt-in |

Standard is the default daily **status and repository-hygiene** check: it does not review implementation source or duplicate code. Full adds implementation tracing and first-party code review where available. freview detects duplicate **work items and deliverables**, never clones or repeated functions; code duplication belongs to the selected official code reviewer.

## Modules

| Area | Questions freview answers |
| --- | --- |
| Discovery | What kind of repository is it? Which policies, stacks, branches and release rules apply? |
| Git | Are branches, worktrees, upstreams, PR ancestry, cherry-picks and candidates coherent? |
| Delivery | Which issue acceptance criteria have real, reachable implementations (Full) or unverified status claims (Standard)? |
| Duplicate work | Which issue/PR pairs, roadmap records or parallel initiatives genuinely represent the same work? Verified versus suspected duplicates are distinct. |
| Remediation | What specifically needs fixing, who owns the work, what is the safest order, and how would success be verified? |
| Verification | Which **exact SHA** was tested, on which matrix, and did every required CI gate pass? |
| Release | Was something merely coded, integrated, verified, or actually published? |
| Hygiene | Are docs, contribution files, license and support policies accurate and discoverable? |
| Dependencies | What package managers/manifests/lockfiles exist, and what does the forge dependency graph show? |
| Accessibility | What limitations, support commitments and human QA gates are documented? |
| Optional specialists | Do installed, approved code-review and security tools add evidence? |

See [SKILL.md](skills/freview/SKILL.md), [modes](skills/freview/references/modes.md), and [report contract](skills/freview/references/report.md).

## Agent aliases and multi-account smoke tests

freview includes a **read-only agent doctor** for Claude Code, Codex, OpenCode, and Antigravity CLI (`agy`). It can recognize named wrappers such as `claude-account1`, `claude-account2`, `opencode1`, and `opencode2` when defined in common shell configuration files, discover their safe literal profile paths, and check **each profile's actual skill directory**, symlink status, and bundled assets:

```sh
python3 skills/freview/scripts/agent_doctor.py --workspace "$PWD"
python3 skills/freview/scripts/agent_doctor.py --format json
```

No AI tokens, shell startup execution, installations, account switching, GitHub calls or filesystem changes. Dynamic wrappers and sourced configuration files may need `--shell-config PATH` and are reported as unresolved rather than guessed. Static presence **does not establish skill activation**; verify through each agent's native skill list. See [agent discovery limitations and safety](skills/freview/references/agent-discovery.md).

## Local work versus GitHub-only review

freview now distinguishes **untracked work**, **staged changes**, **unstaged changes**, **locally committed changes**, **commits ahead of cached upstream**, **other worktrees**, and **live hosted CI/publication evidence**. The local helper reports private status/path metadata but does not read diff bodies or verify a remote push; a Full agent review must inspect the relevant source changes separately. A GitHub-only review explicitly states that local-only work is unobservable. A directory with `git init` but no commits is supported; a non-Git folder needs agent-guided bounded file inspection rather than Git snapshots.

```sh
python3 -I skills/freview/scripts/repo_snapshot.py --json --max-divergences 40
python3 -I skills/freview/scripts/review.py --mode full --format json \
  --expect-identity forge:github.com/raisecaterror/freview
# Opt-in only: status of other worktrees, never their source or full test suites
python3 -I skills/freview/scripts/repo_snapshot.py --json --scan-worktrees --max-worktrees 8
```

The comparison base defaults to a cached remote HEAD if available; this is **not** automatically the real development/integration base. Use `--base` when it is known, and never call cached tracking data definitive proof of a push. Full details: [local-state evidence policy](skills/freview/references/local-state.md).

## Local read-only helper

This is **optional**. It requires Python 3 and Git already installed. From the source checkout:

```sh
python3 skills/freview/scripts/repo_snapshot.py --json
python3 skills/freview/scripts/repo_snapshot.py --base origin/dev
```

The helper reports current Git metadata, worktrees, branch/upstream divergence, dirty state, root-level ecosystem manifests, basic community files and root npm lock alignment. It **never fetches, installs, modifies or deletes** anything. Remote GitHub data, physical QA, software behavior and uncommitted files in other worktrees still require separate evidence.

## Project configuration

Optionally put a validated `.freview.json` at your repository root. Declare your development/release branches, default audit mode, excluded categories, optional human QA gates, bounded audit limits and specialist preferences. The config is **data only**, never executable hooks. See [configuration](skills/freview/references/configuration.md), [JSON Schema](schemas/freview-config.schema.json) and [NMSh example](examples/nmsh.freview.json). Explicit user instructions override project preferences.

## Report semantics and installation checks

Report comparisons now call missing findings `absent_from_new_report` rather than `resolved`. Absence of a finding **does not prove remediation**; verify actual source and CI evidence against exact refs. JSON schema validation checks structure, **not whether a tool really ran**. The report loader bounds reads before parsing and checks timestamps are UTC. Private paths and branch names remain possible in reports; review documents before publication.

The agent installation doctor now checks all bundled references, helpers and template files and examines both documented Antigravity global directories. On aliases it may show `underlying_binary_guess` but **cannot confirm that the wrapper executed that binary**.

## Local JSON reports and daily changes

The optional no-dependency Python CLI can generate local structural metadata in JSON or Markdown:

```sh
python3 -I skills/freview/scripts/review.py --mode standard --format json
python3 -I skills/freview/scripts/review.py --mode full --format markdown
python3 skills/freview/scripts/report_tools.py previous.json current.json --format json
```

The CLI supports Python isolated mode (`python3 -I`), which avoids ambient Python import paths without serving as an operating-system sandbox. The CLI's report is deliberately `local-snapshot`, **not a complete agent review**. The agent produces wider evidence-backed reports following [report JSON Schema](schemas/freview-report.schema.json). An explicit `--output` can write one new file under an approved scratch directory; no files are written by default. To compare daily findings, supply two reports with compatible mode, category scope and integration baseline; the validator refuses incompatible scopes and uses sanitized forge identity or a shared local Git common directory across worktrees. Explicit output files use owner-only permissions.

Agent-generated Full/Partial JSON reports must include a per-category verification manifest; a Full report cannot claim that skipped checks or unperformed code reviews passed. The local helper remains a metadata snapshot, not a completed remote audit.


Before publishing an agent-generated report, run an advisory privacy check (exit code `3` means one or more obvious risks were detected):

```sh
python3 -I skills/freview/scripts/report_tools.py --check-public --format json REPORT.json
```

The checker only names risk **categories**, not the suspected secret values; a clean result **never guarantees that publishing is safe**. Preserve the original privately, manually review issue titles, branch names and diffs, and never auto-upload freview outputs.

## Optional daily automation

See the [scheduled GitHub Actions template](templates/github-actions/freview-daily.yml), which is **not active** until a user deliberately copies/configures it in their own repository. It generates a local Git snapshot, not a paid AI full review. Metadata artifact uploading is **off by default** and requires the explicit `FREVIEW_UPLOAD_ARTIFACT=true` repository variable. For a recurring agent-driven Standard report, configure your preferred scheduler and repository connector separately with explicit authorization. No hosted automation is silently provisioned.

## Specialist delegation

freview includes a curated [specialist registry](catalog/specialists.json) of possible tools (official Anthropic Code Review and OpenAI Codex Code Review; OpenSSF Scorecard, OSV-Scanner, CodeQL, Semgrep, Gitleaks, zizmor and lychee). The registry is *discovery metadata*, not a package installation list or executable plan. It prefers already-installed, trusted tools and uses native review when appropriate; see [specialists](skills/freview/references/specialists.md).

## Findings and remediation plans

Every audit produces both (1) a factual report and (2) a proposed **how-to-fix plan** for confirmed problems. Each action includes the affected issue/PR/ref, supporting evidence, recommended smallest safe repair, priority, prerequisites/owner, verification/QA gates and estimated uncertainty. Nothing is fixed automatically. For a never-implemented *new feature*, freview reports its state and relevant dependency; detailed design or implementation suggestions are **opt-in** with `--suggest-implementation`. An audit must not quietly turn a planned feature into mandatory work.

Duplicate checking compares **issues, PRs, milestones, roadmap entries, release trackers, documentation tasks and overlapping branches/initiatives**. Title similarity is only a candidate signal; confirming duplicates requires a shared deliverable and matching acceptance criteria, not just related topics or branches. Full mode may use source *wiring evidence* to assess whether two delivery initiatives overlap, but leaves duplicate-code/clone detection entirely to official code-review tools.

## Duplicate work with non-closing references and stdin

Issue/PR metadata can be piped through bounded stdin instead of creating a file:

```sh
cat work-items.json | python3 -I skills/freview/scripts/duplicates.py - --format json
```

The checker understands `Closes #N`, `Fixes #N`, `Resolves #N` and **non-closing `Refs #N`/`References #N`** PR-to-issue relationships. A `Refs` link is **not proof the PR implements the issue**; it simply prevents automatically treating an explicitly related PR/issue pair as duplicated delivery. Output remains *candidates only*; no tickets are modified. Pair comparisons are bounded (`--max-comparisons`) and coverage is disclosed as incomplete when a budget is reached. Markdown output escapes terminal control characters.

## Checking duplicate work

The optional metadata-only candidate checker can analyze an exported JSON array of issues, PRs, release tasks, project/roadmap items and documentation records:

```sh
python3 skills/freview/scripts/duplicates.py work-items.json --format json
```

It never fetches GitHub data automatically, never scans duplicate source code, and never marks a candidate as a confirmed duplicate. The **agent-assisted audit** can collect permitted GitHub issue/PR evidence, inspect acceptance criteria, and deliver a separately reasoned recommendation. Related issues, parent/child tasks, backports, and PRs implementing an issue are not automatically duplicates.

## Specialist selection

freview prefers [official Anthropic Code Review](https://claude.com/plugins/code-review) and [OpenAI Codex Code Review](https://help.openai.com/en/articles/20001552-review-pull-requests-with-codex) if those capabilities are actually available. It does **not** recommend `amragl/codebase-review` (3 GitHub stars). Third-party specialists require verified adoption (currently at least 1,000 stars for repository-based tools), current maintenance, quality, suitability and permissions; stars alone are not proof of quality. Official product services need separate entitlement and billing checks. Any review mode that posts GitHub comments or triggers a paid cloud review requires explicit approval.

## Safety

- For untrusted checkouts, prefer a sandbox with no developer credentials. The helper disables known Git execution hooks and configured filters, but **does not provide operating-system isolation**.

- No automatic merges, destructive cleanup, CI setup, issue edits, deploys or dependency installations.
- No presumption that a closed issue means shipped, or an unchecked box means absent code.
- An isolated branch, green local test, published tag and human QA receipt are different states.
- GitHub's **Network graph** illustrates history/forks; its **Dependency graph** concerns package dependencies.
- Respect platform restrictions and user storage/scratch policies. Do not print secrets or publish private source.
- Third-party Agent Skills are executable instructions; inspect them before granting access.

## License and contributing

See [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md). The project is built as a vendor-neutral, reusable skill. NMSh is an example consumer, **not** a built-in requirement.
