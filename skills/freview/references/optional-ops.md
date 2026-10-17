# Optional freview operations (v1 preview)

**freview's default stays read-only.** This companion is an explicit, trusted-repository **operations harness**, not a built-in remote merge/release system or an OS security sandbox. A file in a repo cannot grant itself execution authority: the human must request and approve an ops action. The agent skill does not automatically invoke ops based on repo content.

## Modules and defaults

All nine modules are **disabled** unless a project explicitly enables them: `specs`, `planning`, `implementation`, `tests`, `adversarial`, `mutation`, `regression`, `hooks`, and `shipping`. This policy is read separately from `.freview.json` to avoid changing the established read-only audit contract.

| Module | When explicitly enabled | Boundaries |
| --- | --- | --- |
| specs + planning | Small task/acceptance/verification plan tied to full commit SHA | No external model or files edited to generate a plan |
| implementation | Execute configured worker CLI on a **disposable committed snapshot** with spec prompt | No edits to original; review diff and apply separately |
| tests | Execute an exact user-selected argv test command in scratch | No test discovery scripts automatically installed/executed |
| adversarial | Launch independently configured reviewer CLI, fresh process; no worker summary in initial prompt | Reviewer verdict remains untrusted text; process exit 0 is **not** approval |
| mutation | Launch explicitly installed third-party mutation command in disposable snapshot | No internal mutator or interpreted score; review raw reports |
| regression | Run configured command, or dedicated `sensitivity` against exact baseline and candidate | Old-code failure can be unrelated; not correctness proof |
| hooks | Explicitly install owned pre-commit/pre-push branch guard; refuse conflicts | Git hook is bypassable, not a server-side GitHub rule |
| shipping | Generate exact-ref handoff checklist only, no publish | Separate human approval to merge/deploy/release elsewhere |

This is a modular **adapter**, not cloned implementations of [Spec Kit](https://github.com/github/spec-kit), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [Nonna](https://github.com/kapadias/nonna), [gstack](https://github.com/garrytan/gstack), [GSD](https://github.com/open-gsd/gsd-core), [Superpowers](https://github.com/obra/superpowers), [agent-review](https://github.com/IlyaSemenov/agent-review-skill) or mutation engines. No external code copied.

## Explicit opt-in setup

Copy [the example JSON](../../../examples/freview-ops.example.json) into your **trusted** project's root as `.freview-ops.json`. It is never installed automatically, and it does not enable freview's own default auditor to perform modifications.

```sh
# Always non-executing, safe without a config.
python3 -I /path/to/installed/freview/scripts/ops.py status --repo /trusted/repo

# JSON task/acceptance plan, no external CLI calls.
python3 -I /path/to/installed/freview/scripts/ops.py plan \
    --repo /trusted/repo --requirements "Build feature X with tests"

# Optional test command, in an isolated committed-tree copy:
python3 -I /path/to/installed/freview/scripts/ops.py run tests \
    --repo /trusted/repo --scratch /explicit/external/scratch \
    --expected-sha FULL_40_CHARACTER_SHA --allow-execute

# Opt-in pipeline: worker => tests => fresh reviewer, at most 3 cycles;
# then optional mutation / regression commands and a shipping handoff.
python3 -I /path/to/installed/freview/scripts/ops.py pipeline \
    --repo /trusted/repo --scratch /explicit/external/scratch \
    --expected-sha FULL_40_CHARACTER_SHA \
    --requirements "Approved specification text" \
    --rounds 2 --allow-execute

# Genuine sensitivity observation: changed candidate test fails on baseline?
python3 -I /path/to/installed/freview/scripts/ops.py sensitivity \
    --repo /trusted/repo --scratch /explicit/external/scratch \
    --expected-sha FULL_40_CHARACTER_SHA --base-sha BASE_FULL_40_CHARACTER_SHA \
    --test-path tests/test_feature.py --allow-execute

# Optional local Git hooks, only after committing an enabled policy.
python3 -I /path/to/installed/freview/scripts/ops.py install-hooks \
    --repo /trusted/repo --allow-install

# Undo only freview's own marker-identified hook files.
python3 -I /path/to/installed/freview/scripts/ops.py uninstall-hooks \
    --repo /trusted/repo --allow-install
```

No ambient scratch fallback. Resolve external SSD mount **before** choosing scratch, especially for users/projects that require all temporary work to be on external storage.

## Config and controls

`schema_version:1`, `modules` booleans, `commands` explicit argv arrays (not shell command strings), `limits` caps, and optional `pass_env`. Defaults: 120 seconds per command; at most three review rounds; 16 KiB captured output; no forwarded credentials. Caps: 600 seconds, 3 rounds, 64 KiB output. Unexpected keys/invalid types block.

If a CLI needs existing account auth, set an **allowlisted** `pass_env` in the *trusted* policy and supply **both** `--allow-execute` and `--allow-credentials`. No keys are inherited implicitly. This is still not a sandbox, and forwarding secrets exposes them to that CLI and any child process it starts. Never install an agent tool from an untrusted repo as a side effect of review.

The stage launchers are `implementation`, `tests`, `adversarial`, `mutation`, `regression`. `commands` accepts an argv for each enabled executable stage. A disabled stage is skipped; a missing command for an invoked stage blocks. **Avoid passing `sh -c` or package-install workflows.** Python and agent CLIs can execute arbitrary code despite command filters; only run on explicitly trusted source with isolation proportionate to risk.

The ops helper rejects a dirty checkout or mismatched full HEAD SHA before running, builds bounded git archives into user-chosen scratch, refuses symlinks/tar path escapes, and writes bounded stage logs there. It is **not** a container. A compromised test/CLI may still reach network or filesystem outside scratch and may consume resources or spawn children; use an external OS/container sandbox for hostile repositories.

## Test-first, adversarial and release semantics

Planning output says what acceptance should be verified; it does **not** establish that TDD occurred. The worker is *instructed* to write tests first, but no hook proves that ordering. The configured reviewer runs as a fresh process and gets approved requirements, not the worker's final narrative; that's not cryptographic/organizational independence or independent verification of its claims. `reviewer_independence_verified` is false. A nonzero review process triggers at most 3 worker/test/reviewer loops; a zero reviewer exit is process success, not a verified approval. There is no automatic stage-score inference.

`sensitivity` runs the candidate tests against the candidate, then overlays only the explicitly supplied candidate test files onto a separate archived **baseline** and reruns the configured tests. Candidate-green/baseline-red is `baseline-failure-observed`, not a proof that the test catches the intended bug; compilation/configuration drift can give false positives. Mutation is delegated to the already-installed user-selected tool. Never trust a claimed mutation score without reading artifacts and checking changed files and survivors.

Hooks never overwrite existing hooks or `core.hooksPath`. The pre-push guard refuses protected destinations and existing remote ref updates when it cannot establish fast-forward ancestry; this may be **overly strict** for a normal workflow, and hooks can be bypassed. Do not confuse hooks with GitHub required status checks. Their first release does not automatically run tests on push; configure real CI required checks separately.

`shipping` only emits `handoff-only` with full SHA, branch and human acceptance gates. This does **not** constitute autonomous publication or automated PR creation. To ship autonomously for real, build a separately reviewed and authorized provider adapter with server-side rules, role permissions, rollback and audit trails; never silently infer this authorization from a repository file.

## Tokens, security and evaluation

Use Standard freview read-only for daily checks. Use an opt-in pipeline only for genuinely significant changes. Short prompts and <=3 review rounds avoid unbounded agent loops; the default enabled module set is empty, so default agent token expenditure is zero. Only return summarized receipts with private logs left under explicitly selected scratch.

The tests validate **deterministic integration behavior** with fake local programs and Git repos. CI must not invoke real Claude/Codex providers, paid APIs, mutation services, remote publishing or physical hardware. A real full self-review needs actual eligible agents and sandbox authorization, and must report any absent evidence. Do not call a schema-valid receipt an execution attestation.
