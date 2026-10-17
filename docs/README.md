# freview documentation

Start with the [README](../README.md) for installation, everyday usage and feature overview. freview is an **evidence-first repository auditor**: the default skill is read-only. Its separately configured operations companion can run tools only after explicit authorization.

## Where to go

| Goal | Documentation |
| --- | --- |
| Install into Claude Code, Codex, OpenCode or Antigravity | [Installation and quick start](../README.md#quick-start), [agent discovery and limitations](../skills/freview/references/agent-discovery.md) |
| Understand Quick, Standard and Full | [Review modes](../skills/freview/references/modes.md), [freview skill](../skills/freview/SKILL.md) |
| Interpret local Git status versus remotely observable facts | [Local state and worktrees](../skills/freview/references/local-state.md), [Git analysis](../skills/freview/references/git.md) |
| Check spec completeness and independent verification evidence | [Evidence reconciliation](../skills/freview/references/evidence-reconciliation.md), [verification ground truth](testing/evidence-ground-truth.md) |
| Configure a normal read-only audit | [Project configuration](../skills/freview/references/configuration.md), [audit policy schema](../schemas/freview-config.schema.json) |
| Configure explicitly authorized automated operations | [Operations manual](../skills/freview/references/optional-ops.md), [operations policy schema](../schemas/freview-ops.schema.json), [default-safe example](../examples/freview-ops.example.json) |
| Understand adversarial review claims and interruption recovery | [Reviewer verdict and checkpoints](../skills/freview/references/review-verdict-protocol.md) |
| Use mutation quality, repair budgets and quality gates | [Mutation and autonomy guide](../skills/freview/references/mutation-autonomy.md) |
| Generate or interpret review findings | [Report format](../skills/freview/references/report.md), [remediation](../skills/freview/references/remediation.md) |
| Configure daily, optional checks | [Automation](../skills/freview/references/automation.md) |
| Diagnose installation/agent discovery | [Agent doctor and paths](../skills/freview/references/agent-discovery.md), [native activation acceptance checklist](testing/agent-activation-acceptance.md), [support](../SUPPORT.md) |
| Contribute or report a problem | [Contributing](../CONTRIBUTING.md), [support](../SUPPORT.md), [security reporting](../SECURITY.md) |
| See the evidence and historical development record | [Audit archive](audits/README.md), [historical roadmaps](roadmap/) |

## Two different configurations

**`.freview.json`** is optional, non-executable audit preference data. It can help choose the scope and branches for a normal read-only review. It never grants permission to run project scripts.

**`.freview-ops.json`** is an entirely separate, versioned policy for *opt-in* operations: trusted worker and reviewer commands, tests, mutation tools, local hooks and a shipping **handoff**. Every execution-capable module is disabled by default. Enabling a module in a file alone cannot grant execution permission; runtime execution requires explicit user authorization, a clean exact-SHA checkout and caller-selected scratch storage. Never assume that copying the example turns autonomy on.

## Current readiness and limitations

- **Usable from source now:** the skill, reference documents and Python 3/Git helpers are on `main`. No versioned GitHub release has been published. Use the [installation instructions](../README.md#quick-start) and verify native skill discovery in the actual client.
- **Verified in CI:** the bundled assets, schema contracts, deterministic helper tests and isolated fake-agent workflows have passed Ubuntu and macOS matrix checks for the integrated `main` branch.
- **Not established by CI:** live Claude/Codex/OpenCode/Antigravity invocation for every supported client, real Stryker/mutmut workloads, arbitrary external tool safety, production deployment and physical Mac/SSD acceptance. They remain **acceptance gates for claims about those environments**, not evidence that the default read-only skill has failed.
- **Security boundary:** scratch copies are not operating-system sandboxes; a configured executable may still access other files and the network. Keep untrusted code outside optional execution unless separately sandboxed.

## Historical documents versus current state

The [audit archive](audits/README.md) and `docs/roadmap/` are **Historical** records. A dated entry that says a PR was a draft or unmerged describes its state *at that checkpoint*, not its current GitHub state. Feature PRs [#16](https://github.com/raiseCatError/freview/pull/16) through [#20](https://github.com/raiseCatError/freview/pull/20), plus the configuration-standardization [#21](https://github.com/raiseCatError/freview/pull/21), have since merged into `main`.

Do not silently rewrite source-level audit findings, past SHAs or test evidence. Verify current Git refs and CI separately when making a present-day claim.
