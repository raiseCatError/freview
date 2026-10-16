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
freview                                  # Ask quick / standard / full; standard default
freview quick                            # Rapid factual snapshot
freview standard                         # Daily useful hygiene/status check
freview full                             # Complete applicable structural audit
freview full excluding security, docs    # Exclude selected categories
freview only git, issues, releases       # Target specific categories
freview full --with code-review          # Opt into deeper code-quality review
freview full --with security-scan         # Opt into an authorized specialist scan
freview full --base release/next         # Explicit candidate baseline
```

The assistant asks **one concise scope question** only when needed; if running unattended it picks standard and states what it assumed.

**Important:** “full” means the widest applicable *status/evidence* audit. It does **not** silently execute expensive test suites, arbitrary repository scripts, third-party scanners or an automated code refactor. Code review and external security scans are explicit opt-ins.

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

## Safety

- No automatic merges, destructive cleanup, CI setup, issue edits, deploys or dependency installations.
- No presumption that a closed issue means shipped, or an unchecked box means absent code.
- An isolated branch, green local test, published tag and human QA receipt are different states.
- GitHub's **Network graph** illustrates history/forks; its **Dependency graph** concerns package dependencies.
- Respect platform restrictions and user storage/scratch policies. Do not print secrets or publish private source.
- Third-party Agent Skills are executable instructions; inspect them before granting access.

## License and contributing

See [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md). The project is built as a vendor-neutral, reusable skill. NMSh is an example consumer, **not** a built-in requirement.
