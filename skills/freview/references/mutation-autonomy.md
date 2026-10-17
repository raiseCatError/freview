# Mutation quality and bounded autonomy (opt-in)

**Default:** no mutation tool, no coding agent, no test execution, no hooks and no shipping are invoked by the standard `/freview` audit. Everything below is only for a trusted repository with explicit `.freview-ops.json` policy plus the execution permission flags described in [optional operations](optional-ops.md).

## What freview implements

Mutation **execution** is delegated to a user-selected, already-installed engine such as [StrykerJS](https://stryker-mutator.io/docs/stryker-js/incremental/) or [mutmut](https://mutmut.readthedocs.io/en/latest/). freview implements the portable quality **interpretation and gating layer**: consumes a bounded report, validates expected structure and freshness in that exact disposable verifier workspace, counts Killed + Timeout as detected and Survived + NoCoverage (mutmut `no_tests`) as undetected, and reports representative survivor locations where available. A mutation tool returning exit code zero **without a fresh structured report does not pass**. Stryker's Pending or mutmut's interrupted/suspicious results are inconclusive. mutmut currently exports totals that may include categories omitted from its CI JSON (such as not-checked or caught-by-type-check); freview exposes those as **unclassified** and does not pretend the run is complete.

**Not a proof of correctness.** Report JSON and mutation engine output can be misleading; mutmut CI summary has aggregate counts only, not per-mutant locations, and surviving/equivalent mutants need human interpretation. For every report freview records the engine format, observed score, counts, advisory/gate decision, and limitations. It never copies or executes commands suggested by a report.

## Configuration

All module switches are **false by default**. An explicitly opted-in example with a mutation-quality gate and bounded repair automation:

```json
{
  "schema_version": 1,
  "modules": {
    "tests": true,
    "adversarial": true,
    "implementation": true,
    "mutation": true,
    "shipping": true
  },
  "commands": {
    "tests": ["python3", "-m", "unittest", "discover", "-s", "tests"],
    "implementation": ["/trusted/bin/worker-agent"],
    "adversarial": ["/trusted/bin/reviewer-agent"],
    "mutation": ["python3", "/trusted/freview/skills/freview/scripts/mutmut_driver.py"]
  },
  "mutation_quality": {
    "format": "mutmut",
    "mode": "gate",
    "min_score": 70,
    "min_valid_mutants": 5,
    "max_survivors": 12
  },
  "autonomy": {
    "max_stage_runs": 12,
    "stop_on_no_progress": true,
    "max_repeated_findings": 1,
    "require_mutation_for_shipping": true
  },
  "limits": {
    "timeout_seconds": 120,
    "max_rounds": 2,
    "max_output_bytes": 16384
  }
}
```

Replace every sample path and command with **an already-installed, trusted executable**. This is a policy example, not something freview creates or enables automatically. The worker and reviewer need compatible noninteractive adapters, and *must* have authorization. `mutmut_driver.py` runs `mutmut run` followed by `mutmut export-cicd-stats` without using a shell; it neither installs mutmut nor guarantees mutations can run on every codebase.

Alternatively, for StrykerJS, configure an already-installed `./node_modules/.bin/stryker` executable with `["./node_modules/.bin/stryker", "run", "--reporters", "json"]` and `mutation_quality.format="stryker"`; it must emit a standard `reports/mutation/mutation.json` file. Scope costly mutation runs to changed, high-risk code when the engine supports it. Stryker incremental mode can save work, but its change detection is not infallible when dependencies/environment change; `--force` is useful for a fresh scoped verification. Do not run `npm install`, `pip install` or download packages during a default audit.

## Default behavior and tuning

| Setting | Default | What it does |
| --- | --- | --- |
| Mutation module | **off** | No mutator runs |
| `mutation_quality.format` | `auto` | Recognize the two fixed report paths; ambiguous/missing is invalid or inconclusive |
| `mutation_quality.mode` | `advisory` | Show score without a threshold-enforced gate; **missing or incomplete evidence still blocks** |
| `mutation_quality.min_score` | 60 | Default advisory target; enforced only in `gate` mode |
| `mutation_quality.min_valid_mutants` | 1 | A zero-valid-mutant report is never treated as perfect |
| `mutation_quality.max_survivors` | 12 | Bounded survivor hints, not complete raw source |
| `autonomy.max_stage_runs` | 12 (maximum 32) | Whole-pipeline cap across planning, worker, tests, reviewer, regression, mutation |
| `autonomy.stop_on_no_progress` | `true` | Stop if worker does not change source after receiving actionable review feedback |
| `autonomy.max_repeated_findings` | 1 | Stop unchanged repeated finding signatures to avoid expensive oscillations |
| `autonomy.require_mutation_for_shipping` | `false` | Optional stricter *handoff-only* gate requiring a scored passing mutation run |
| `limits.max_rounds` | 3 (maximum 3) | Hard ceiling on review/fix iterations |

**Safety note:** Even if a mutation score clears the configured gate, this only clears an optional checklist item. Production source is never auto-merged, committed, pushed or deployed by this layer. `shipping` returns a human handoff rather than an actual release.

## Evidence, status and recovery

- An enabled mutation program with exit code 0 but missing, stale, malformed or interrupted report produces `mutation-inconclusive`.
- With `mode="gate"`, a complete report below score or minimum valid-mutant threshold produces `mutation-threshold-failed`. In advisory mode, a *complete* low-scoring report is shown with `quality_pass=false`, but does not block the **human handoff** unless `require_mutation_for_shipping` is enabled.
- Any stage exceeding the configurable global cap yields `budget-exhausted` before launching another subprocess.
- A worker that receives findings and leaves the candidate unchanged yields `no-progress`. Repeated identical findings despite edits yield `stalled-review-findings`.
- Tests are run in a separate verifier copy of the current candidate; mutation programs can edit only their own verifier copy (unless they break OS-level boundaries). The original source SHA and source changes are kept distinct from test/mutant artifacts.
- Scratch `checkpoint.json` includes mutation score/counts and the fresh-report observation. A checkpoint is **not a signed attestation or a runnable resume**. Use `ops.py inspect-checkpoint --checkpoint FILE` to inspect only, and re-run exact-SHA tests after integrating any generated changes.

Execution still requires `--allow-execute`, a clean immutable source commit, explicit `--scratch`, and `--allow-credentials` if the policy explicitly requests any environment secrets. **A cloned file tree is not an OS/container sandbox.** Do not execute untrusted repositories without additional isolation. For external-SSD-only project policies, select a verified mounted scratch path and never silently fall back to internal storage.

## Honest acceptance boundary

CI fixtures cover parser edge cases, fake mutator CLI commands and local-Git stage budgets on Ubuntu/macOS. They do **not** demonstrate paid model-provider invocation, real survivor-killing tests, signed provenance, prompt-injection resistance of arbitrary agents, real mutation workloads, or production autonomous deployment. Those are separate host-level and human release gates.
