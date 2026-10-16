# freview

**Full repository review, without guessing what “done” means.**

freview is a portable, evidence-first [Agent Skill](https://agentskills.io/) for assessing the *actual state* of a repository. It discovers how the project works before examining its Git history, worktrees, issues/PRs, implementation reachability, exact-commit CI, release process, documentation, community standards, dependencies and accessibility. It can optionally coordinate specialist code-quality and security reviews, **without copying their functionality**.

It produces a review, not a cleanup script. Default operations are **read-only**.

> **Status:** v0.1 preview in [draft PR](https://github.com/raiseCatError/freview/pulls). Installation commands below will work from the public default branch **after the skill PR is merged**. Until then, install directly from the review branch only for testing.

## Install

One portable skill: `skills/freview/SKILL.md`, with references and an optional Python-standard-library snapshot helper.

Recommended, using the [open `skills` installer](https://github.com/vercel-labs/skills):

```sh
# Install into your current project (choose supported agents when prompted)
npx skills add raiseCatError/freview --skill freview

# Or make it available across your projects
npx skills add raiseCatError/freview --skill freview -g
```

The `skills` installer supports Claude Code, Codex, OpenCode, Gemini and many other agents. It can create symlinks or copies depending on selected agent and platform; review permissions before installing. Run `npx skills add raiseCatError/freview --list` to inspect discovered skills without installing them. No official provider endorsement is implied.

Gemini CLI also offers a native installation workflow:

```sh
gemini skills install https://github.com/raiseCatError/freview --path skills/freview
```

Codex's native skill installer can install a GitHub repo path; OpenCode discovers `.agents/skills/freview/`; Claude Code supports project and user skill directories. Use agent-specific installation only if your installed version supports the required path.

## Use

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
```

By default freview runs Standard, without unnecessary questions. It asks only when a missing essential detail or permission requires a decision. Project policy may set a different default.

**Important:** Full includes a deep code-quality review, using a trusted installed specialist when appropriate or a bounded native review otherwise. Standard is the recommended daily check **without deep code review**. Full never silently installs tools, executes arbitrary scripts, runs expensive test suites, uploads private code, edits files or invokes external vulnerability scanners; those scanners remain opt-in.

## Modules

| Area | Questions freview answers |
| --- | --- |
| Discovery | What kind of repository is it? Which policies, stacks, branches and release rules apply? |
| Git | Are branches, worktrees, upstreams, PR ancestry, cherry-picks and candidates coherent? |
| Delivery | Which issue acceptance criteria have real, reachable implementations? |
| Verification | Which **exact SHA** was tested, on which matrix, and did every required CI gate pass? |
| Release | Was something merely coded, integrated, verified, or actually published? |
| Hygiene | Are docs, contribution files, license and support policies accurate and discoverable? |
| Dependencies | What package managers/manifests/lockfiles exist, and what does the forge dependency graph show? |
| Accessibility | What limitations, support commitments and human QA gates are documented? |
| Optional specialists | Do installed, approved code-review and security tools add evidence? |

See [SKILL.md](skills/freview/SKILL.md), [modes](skills/freview/references/modes.md), and [report contract](skills/freview/references/report.md).

## Local read-only helper

This is **optional**. It requires Python 3 and Git already installed. From the source checkout:

```sh
python3 skills/freview/scripts/repo_snapshot.py --json
python3 skills/freview/scripts/repo_snapshot.py --base origin/dev
```

The helper reports current Git metadata, worktrees, branch/upstream divergence, dirty state, root-level ecosystem manifests, basic community files and root npm lock alignment. It **never fetches, installs, modifies or deletes** anything. Remote GitHub data, physical QA, software behavior and uncommitted files in other worktrees still require separate evidence.

## Project configuration

Optionally put a validated `.freview.json` at your repository root. Declare your development/release branches, default audit mode, excluded categories, optional human QA gates, bounded audit limits and specialist preferences. The config is **data only**, never executable hooks. See [configuration](skills/freview/references/configuration.md), [JSON Schema](schemas/freview-config.schema.json) and [NMSh example](examples/nmsh.freview.json). Explicit user instructions override project preferences.

## Local JSON reports and daily changes

The optional no-dependency Python CLI can generate local structural metadata in JSON or Markdown:

```sh
python3 skills/freview/scripts/review.py --mode standard --format json
python3 skills/freview/scripts/review.py --mode full --format markdown
python3 skills/freview/scripts/report_tools.py previous.json current.json --format json
```

The CLI's report is deliberately `local-snapshot`, **not a complete agent review**. The agent produces wider evidence-backed reports following [report JSON Schema](schemas/freview-report.schema.json). An explicit `--output` can write one new file under an approved scratch directory; no files are written by default. To compare daily findings, supply two reports with compatible coverage; the validator will refuse incomparable scopes.

## Optional daily automation

See the [scheduled GitHub Actions template](templates/github-actions/freview-daily.yml), which is **not active** until a user deliberately copies/configures it in their own repository. It generates a local Git snapshot, not a paid AI full review. For a recurring agent-driven Standard report, configure your preferred scheduler and repository connector separately with explicit authorization. No hosted automation is silently provisioned.

## Specialist delegation

freview includes a curated [specialist registry](catalog/specialists.json) of possible tools (codebase-review, OpenSSF Scorecard, OSV-Scanner, CodeQL, Semgrep, Gitleaks, Markdownlint, lychee and more). The registry is *discovery metadata*, not a package installation list or executable plan. It prefers already-installed, trusted tools and uses native review when appropriate; see [specialists](skills/freview/references/specialists.md).

## Safety

- No automatic merges, destructive cleanup, CI setup, issue edits, deploys or dependency installations.
- No presumption that a closed issue means shipped, or an unchecked box means absent code.
- An isolated branch, green local test, published tag and human QA receipt are different states.
- GitHub's **Network graph** illustrates history/forks; its **Dependency graph** concerns package dependencies.
- Respect platform restrictions and user storage/scratch policies. Do not print secrets or publish private source.
- Third-party Agent Skills are executable instructions; inspect them before granting access.

## License and contributing

See [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md). The project is built as a vendor-neutral, reusable skill. NMSh is an example consumer, **not** a built-in requirement.
