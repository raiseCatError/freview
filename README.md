# freview

**Full Review**, pronounced **“f-review”** (the letter **F**, then *review*). Not “free-view” or “fre-view”.

**Audit the repo, not the summary.**

Full repository review, without guessing what “done” means.

freview is a portable, evidence-first [Agent Skill](https://agentskills.io/) for assessing the *actual state* of a repository. It discovers how the project works before examining its Git history, worktrees, issues/PRs, implementation reachability, exact-commit CI, release process, documentation, community standards, dependencies and accessibility. It can optionally coordinate specialist code-quality and security reviews, **without copying their functionality**.

It produces a review, not a cleanup script. Default operations are **read-only**.

> **Status:** Pre-release read-only preview for trusted repositories; **no version has been tagged or published**. Installation and native discovery depend on agent/runtime configuration. A Full review is not a security certification or physical-device verification.

**Pre-evidence-reconciliation baseline:** [PR #14](https://github.com/raiseCatError/freview/pull/14) merged at [`b4e9de58`](https://github.com/raiseCatError/freview/commit/b4e9de581107b8b78b4a710a5be93fa4e90510e8), with [99 Python tests passing on both Ubuntu and macOS](https://github.com/raiseCatError/freview/actions/runs/38983887532). User-provided field evidence reports native invocation in Antigravity CLI, Claude Code, Codex and OpenCode; this is **not** four independently re-executed Full audits, and OpenCode's full five-gate acceptance matrix remains unobserved.

**In-progress enhancement:** [draft PR #16](https://github.com/raiseCatError/freview/pull/16) introduces optional specification inventory, verification-receipt consistency checks, evidence-aware reports and deliberately deceptive metadata fixtures. It remains pre-release; CI and author review are not independent runtime-agent acceptance.

**Dogfooding:** [final pre-release freview-on-freview review](docs/audits/2026-10-17-final-pre-release-self-review.md) · [historical original audit](docs/freview-reviews-freview.md). The newer source review is a bounded, hosted-evidence **partial-audit**, not native invocation in the author's agent session.

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

## Requirements and verification evidence

freview now includes optional, dependency-free tools for **candidate specification discovery** (OpenSpec / Spec Kit metadata) and **verification receipt consistency**. The scope is deliberately narrow: an inventory does not establish a requirement, and a receipt cannot authenticate a test run or independent reviewer.

```sh
python3 -I skills/freview/scripts/spec_inventory.py --root .
python3 -I skills/freview/scripts/receipt_check.py receipt.json --expected-sha FULL_40_CHARACTER_SHA
```

The second command inspects a supplied JSON receipt and never runs its test command. Agent-generated reports may optionally list per-requirement evidence; `report_tools.py old.json new.json --format json` then highlights changed or missing claim evidence without pretending absent claims are resolved. A reference can be coherent yet unverified; failing, mismatched and incomplete evidence are reported separately. In a Full review, the agent may reconcile approved specification scenarios with implementation, test quality, exact-head CI, integration, and publication. **Actual independent test reruns, mutation analysis, tool installation, worktree changes, or merge gating require separate permission** and an isolated environment. See the [evidence-first audit protocol](skills/freview/references/evidence-reconciliation.md) and [durable design checkpoints](docs/roadmap/evidence-reconciliation-2026-10.md).

## Optional operations: everything off by default

The preview [freview ops companion](skills/freview/references/optional-ops.md) adds **separately enabled** specification/plan generation, worker CLI invocation, isolated test execution, fresh-process **structured JSON** adversarial reviewer verdicts (up to 3 bounded repair cycles), mutation-tool delegation, exact-commit baseline regression sensitivity, local Git hook guards and human shipping handoff. These are **not part of the default read-only audit**. No untrusted repository configuration can silently authorize execution, install tools or publish releases.

```sh
# No config = all modules disabled, no execution or tokens
python3 -I skills/freview/scripts/ops.py status --repo .

# Copy examples/freview-ops.example.json into a *trusted* repo and deliberately
# enable chosen modules/argv, commit the policy, then inspect invocation permissions and scratch.
python3 -I skills/freview/scripts/ops.py plan --repo . --requirements "Desired behavior"
# See the full guide for --scratch, --expected-sha and --allow-execute.
```

A completed reviewer process cannot approve itself with plain text: freview validates exact source/workspace identity and retains [non-resuming atomic scratch checkpoints](skills/freview/references/review-verdict-protocol.md). The helper runs the worker in a **disposable committed-tree candidate**, then tests, reviewers and mutation tools in their own **fresh verification copies** (all under explicitly approved scratch), never in the original checkout. Test caches do not count as worker changes; a test modifying pre-existing source files or a reviewer modifying its copy blocks its respective gate. This is isolation of files, **not a secure OS sandbox**. Real Claude/Codex tokens/accounts, native agent activation, mutation scores, correctness, real release authorization and cross-agent independence remain separately verifiable and are **not** certified by synthetic CI fixtures. When a worker modifies the disposable source snapshot, freview records its workspace fingerprint and **blocks the shipping handoff until those edits are integrated and independently checked**. Shipping is a handoff, not an automated push, merge or deployment. [Design and recovery journal](docs/roadmap/optional-ops-2026-10.md).

### Mutation-quality gates and bounded autonomy (opt-in)

The ops companion now understands Stryker JSON and mutmut CI stats **as actual mutation evidence**, rather than trusting a mutator's exit code alone. It reports detected, surviving/no-coverage, pending and unknown mutants, plus a bounded sample of survivor locations. Missing, stale, interrupted or malformed reports are inconclusive; a separately enabled score gate can block a handoff. The portable mutmut runner invokes an **already-installed** mutmut CLI and exports its stats without a shell.

Worker/reviewer loops additionally enforce a **global subprocess budget** and stop when a worker makes no source progress or repeated findings remain unchanged. All behavior is explicitly configurable; all modules remain OFF by default. Scratch checkpoints retain evidence without automatically resuming or signing an audit. See the [mutation and autonomy guide](skills/freview/references/mutation-autonomy.md) and [configuration example](examples/freview-ops.example.json).

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
