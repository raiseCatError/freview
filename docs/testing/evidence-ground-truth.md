# Evidence reconciliation: labeled ground-truth fixtures and limits

**2026-10-17 — Checkpoint C4.** This is a *deterministic local metadata-contract test*, not a benchmark of freview's live agent effectiveness, external review tools, model quality or the correctness of arbitrary implementations. Do not advertise fixture pass counts as accuracy against real projects.

## How to reproduce

```sh
python3 -m unittest tests/test_adversarial_scenarios.py -v
# Portable full suite (also CI):
python3 -m unittest discover -s tests -v
```

The fixture input lives in `tests/fixtures/evidence_scenarios.json`. No network, paid agents, package installation or test commands from the fixture are executed. A test command inside a receipt is untrusted **text**.

## Pre-labeled ground truth

| Trap / claim | Expected result | Intentional limitation |
| --- | --- | --- |
| Worker reports passing tests with named CI URL | `claimed-evidence` | URL/text isn't fetched or authenticated; no assertion tests actually ran |
| Worker reports done, exit code nonzero | `failed` | Detects admission of failure, not a lie in a forged receipt |
| Green result at other SHA / mismatched expected SHA | `contradictory` | Exact SHA mismatch; no inference on cherry-pick equivalence |
| Passing tests but empty evidence list | `incomplete` | Absence of reference is not success |
| Claimed independent actor | `claimed-evidence` plus warning | Independent author identity cannot be authenticated by JSON |
| Green receipt after worker rewrote tests to pass | `claimed-evidence` (**known miss**) | Needs source diff review, baseline regression sensitivity or approved mutation checks |
| Empty test command | `invalid` | Schema-level rejection only |
| OpenSpec candidate paths | `inventory-only` | No source content or implementation checked |
| Generic `specs/` folder | `inventory-only` candidate (**known possible false positive**) | Path layout not proof project uses Spec Kit |
| No known spec directories | `no-known-artifacts` | Requirements may exist in tickets, ADRs, external trackers or other naming conventions |

The tests intentionally assert that these two **known limitations persist as disclosed** rather than converting them to false claims of detection.

## Already-covered Git and worktree scenarios

Existing `tests/test_repo_snapshot.py` creates isolated real local Git fixtures for staged/unstaged/untracked changes, local commits with no upstream, commits ahead of a cached upstream, divergent branches and other worktrees. These tests already distinguish **cached tracking information** from **actual remote publication proof**. They do not demonstrate access to a different user's unmounted checkout or remote live state. Avoid duplicating Git fixtures for the sake of inflated case counts.

## Independent adversarial auditing remains opt-in

The Reddit-inspired stronger procedure is documented in `skills/freview/references/evidence-reconciliation.md`:

1. Read original requirements and candidate SHA without first accepting worker summaries.
2. Obtain exact worker test commands, exit codes, log/JUnit artifacts and source SHA.
3. Independently inspect/test only with permission, safe isolated storage, bounded resources and no production credentials.
4. Assess weakened/skipped/deleted tests and compare regression tests with the baseline; optionally use mutation testing when expressly approved.
5. Return *blocked/unverified* when evidence, permissions or environment are missing, and do not configure merges by implication.

We have **not** executed Spec Kit convergence, OpenSpec verification, Nonna's agent hooks, gstack, paid official reviewers, independent mutation frameworks, or real-world agent tasks as part of this fixture benchmark. Their relative defect detection and cost cannot be inferred from these synthetic metadata cases. The current codebase is not a merge-blocking runtime, an attestation provider or proof of correct software.

## Product decision

**Audit the repo, not the summary.**

Initial audience: maintainers/solo builders who use several coding agents across local and GitHub work, and need factual reconciliation between requirements, source, verification receipts, integration and release status. Keep freview as a read-only independent coordinator, not a competitor to spec lifecycle tools, reviewer plugins or automatic hook enforcement.

Priority for a later separately authorized phase: evaluate real manually labeled repos and fresh independent agents, compare outputs against Spec Kit/OpenSpec/gstack/Nonna where appropriate, and measure false positives, actionable discoveries, token cost and installation reliability. Only then consider any installer, hosted service, background CI gate, tool vendoring or paid offering. **MIT permission is not justification to import unused code.**

## Privacy and CI

The fixture contains fake repository names, synthetic SHAs and synthetic URLs. No private user paths or secrets need to be committed. Before publishing live reports, run the existing advisory privacy lint and review findings manually. Exact-head CI validates only the code/version it actually checked; do not extrapolate it to later commits, platforms outside the matrix, security certification or native client invocation.
