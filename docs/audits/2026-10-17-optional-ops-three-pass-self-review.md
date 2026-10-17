# freview optional operations — three bounded review passes

**Date:** 2026-10-17 UTC. **Branch:** `feature/opt-in-ops-20261017`.
**PR:** [#17](https://github.com/raiseCatError/freview/pull/17) stacked on draft [#16](https://github.com/raiseCatError/freview/pull/16).
**Classification:** *bounded GitHub-hosted native source/CI audit*, **not three independently executed agent reviews** and not native self-invoked freview skill acceptance. This session has GitHub file/CI access but no user's Mac worktree or authenticated Claude/Codex/OpenCode runtimes. The tests use synthetic local Git repositories and fake CLI programs; no paid agent, mutation engine or actual release is invoked.

## Product acceptance

**Audit the repo, not the summary** stays the primary independent read-only skill. `ops.py` is an opt-in companion, not the default and not a second general purpose lifecycle framework. All modules OFF without a trusted `.freview-ops.json`. Separate explicit execution/credentials/hook permissions. No merge, tag or publication.

Competitive boundaries:
- Spec Kit / OpenSpec: adopt spec-first acceptance contracts and artifact interoperability, not their whole authoring frameworks.
- GSD / gstack / Superpowers: adopt checkpointed plan → implement → test → review → handoff lifecycle.
- Nonna: adopt opt-in local test/branch protection, without copying its provider hooks.
- agent-review / review-loop: bounded challenge/refinement rounds with fresh review process; **no claims of model independence** without observed runtime verification.
- mutmut / Stryker: integrate externally selected tool through argv; no fake native mutation engine.

No external source code was copied. This tranche uses Python standard library only.

## Round 1 — semantics and functional correctness

**Findings accepted/fixed:**
1. A disabled/no-test pipeline could have said `checks-executed` and offered shipping handoff. **Fix:** any pipeline must enable a configured test stage; no check, no handoff. Standalone plan works without tests because it is not verification.
2. Enabled executable stage with missing argv could allocate a disposable checkout before blocking. **Fix:** reject missing executable configuration and denied credentials prior to snapshot creation.
3. Planning was only a static checklist with no model adapter. **Fix:** optional `planning` subprocess runs in a disposable snapshot, with bounded input; default static plan remains zero tokens and read-only.
4. Evidence from reviewer exit code could be mistaken for approval. **Clarification:** subprocess `passed` is exit-code success only, `reviewer_independence_verified=false`, and no result certifies correctness.
**Tests:** `test_optional_ops.py` all-default-off, no-test pipeline, explicit planning stage, up to 3 passes, exact ref, and shipping handoff.
**CI evidence:** [R1 run](https://github.com/raiseCatError/freview/actions/runs/38989576647) at `3717bf28`, Ubuntu/macOS success.

## Round 2 — hostile inputs and resource isolation

**Findings accepted/fixed:**
1. First git archive code wrote the entire archive before rejecting oversized inputs. **Fix:** cap bytes while streaming; stop and terminate the archive process before exceeding scratch budget. A regression uses an artificially small cap.
2. First runner collected all process output into memory before slicing. **Fix:** selector-driven capped reads; oversize is `output-limit`, not success; bound logs.
3. A killed parent could leave orphan subprocesses. **Fix:** create a new process group and kill the group on resource violation; test a child that would write an unauthorized marker after its parent is stopped.
4. Symlink/tar extraction and hostile workspace permissions. **Disposition:** reject archive symlinks, special files and traversal; cap members and expanded bytes; use explicit user-provided scratch. Still no OS sandbox against code accessing host/network or concurrent filesystem races.
**Tests:** R2 archive cap and child-process termination, plus prior Git status/worktree and symlink fixtures.
**CI evidence:** [R2 run](https://github.com/raiseCatError/freview/actions/runs/38989757284) at `c2402a86`, Ubuntu/macOS success.

## Round 3 — Git hooks, source integrity and releasing

**Findings accepted/fixed:**
1. Initial install used `rev-parse --git-path hooks` after forcing `core.hooksPath`, so it resolved the wrong path. **Fix:** use Git common directory and preserve existing hook files.
2. First pre-push guard blocked all updates to existing feature refs, including ordinary fast-forward pushes. **Fix:** accept updates only if Git can prove the old SHA is an ancestor of local SHA; refuse protected refs/deletions/unknown ancestry.
3. No pre-push test enforcement despite enabled test module. **Fix:** when `hooks` and `tests` are both enabled, pre-push requires `FREVIEW_OPS_SCRATCH` and reruns configured tests from an exact clean snapshot; denied/missing scratch fails closed.
4. Simulated Git pre-push fixture encoded a literal backslash-n; thus the supposed valid ref update failed parsing. **Fix:** newline-terminate the fixture correctly. Test commands are not evidence until the test fixtures themselves make sense.
5. A worker can edit the disposable workspace while receipts still reference the **original Git SHA**. **Fix:** record before/after workspace fingerprints and block shipping inference with `implementation-not-integrated` whenever scratch differs from the committed snapshot. This is not an attestation of a new candidate commit. A test deliberately writes a new implementation file in scratch and checks that neither source repo nor shipping handoff changes.
6. Unrequested auto-publishing would be unsafe. **Disposition:** `shipping` is a **handoff-only** module. It cannot push, merge, release or deploy. A real provider shipping adapter requires separate permissions, rollback planning, and protected-branch server-side checks.
**Tests:** hook install/uninstall preserving existing hooks; new ref, fast-forward vs force; pre-push tests enabled only with scratch; no-test pipeline cannot claim success.
**CI evidence:** Final exact-head run **must be checked after the last documentation commit**, as a run at an earlier SHA never certifies the final tree.

## Verification manifest / what remains unobserved

| Capability | Actual source/CI coverage | Not established |
| --- | --- | --- |
| Read-only policy defaults | Unit tests / code inspection | Untrusted runtime extension or malicious repo OS sandbox |
| Project spec source discovery | Prior PR #16 tests / helper | True spec completeness or native OpenSpec/Spec Kit convergence |
| Test execution | Synthetic isolated programs at exact SHA | Real user's tests, external APIs, app UI or hardware |
| Planning and implementation | Opted argv program in disposable snapshot | LLM integration end-to-end, correctness or automatic application to main |
| Adversarial review | Fresh configured process, capped loop | Separate model/account, independent review truth, reviewer findings interpreted |
| Mutation tests | Optional configured command + bounded log | Actual mutation score/survivors or test quality certification |
| Regression sensitivity | Candidate tests copied over baseline + rerun | Semantic fault isolation; old-code failure may be unrelated |
| Hooks | Local Git fixture + shell script guard | GitHub required checks, unbypassable protection, workflows with pre-existing hooks |
| Shipping | Evidence-labeled human handoff | Real PR publishing, merge, tag, deployment or production rollback |

## Release verdict and handoff

**Provisional result:** useful first-party, standard-library, opt-in companion with bounded capabilities; not a replacement for Nonna/gstack/OpenSpec/Stryker, not a general OS sandbox and not an autonomous release service. No final release approval. Final branch-head CI and manual review required before stacked PR merge. Do not represent this document as independently executed freview Full or three model-to-model adversarial audits.

Owner next steps: authorize controlled local smoke on the actual host with chosen external SSD scratch; review provider argv/credentials; run native Claude/Codex/OpenCode agent processes separately in their supported sandbox; inspect mutation and baseline logs; wire enforceable server-side checks if desired; and only then decide whether to merge, tag or publish.
