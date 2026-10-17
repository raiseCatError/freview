# freview adversarial review verdict protocol (v1)

**Audit the repo, not the summary.** This is the on-disk JSON protocol for an explicitly invoked *optional operations* reviewer, not for freview's default read-only audit.

## What changed

A reviewer CLI returning exit code 0 is **not** approval. A successful reviewer stage now needs **one valid JSON object on standard output**, referencing the exact *original* source SHA and actual *disposable workspace* SHA-256 fingerprint supplied to the reviewer.

The runner constructs its review prompt from **approved requirements and inspected workspace identity**, never from the worker's summary. Reviewers are instructed not to modify the workspace. If they do, the stage is rejected. A reviewer JSON claim does **not** prove separate identity, source reading, effective tests, or code correctness.

## Reviewer output

```json
{
  "schema_version": 1,
  "source_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "workspace_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "verdict": "changes_requested",
  "reviewed_paths": ["src/example.py", "tests/test_example.py"],
  "reason": "An edge-case regression is missing",
  "findings": [
    {
      "id": "R1",
      "severity": "high",
      "path": "src/example.py",
      "description": "Empty input returns an incorrect value",
      "evidence": "src/example.py:18 lacks the documented empty-input guard"
    }
  ]
}
```

The **real** SHA and digest come from the runner's `SOURCE_SHA:` and `WORKSPACE_DIGEST:` markers, not this illustrative document. `verdict` is exactly `approve`, `changes_requested` or `blocked`. `approve` **must** have zero outstanding findings; `changes_requested` **must** have at least one. Findings must identify actual observed relative paths (no traversal, symlinks or phantom files), a stable ID, severity, bounded description and evidence. `reason` must be nonempty. Unknown fields, duplicated keys, malformed JSON, nonzero reviewer process status or truncated output all block acceptance.

Accepted output is labeled `reviewer-approved-claim`; **never** `independently-verified`. The report keeps `reviewer_independence_verified=false` and `source_reading_verified=false`.

## Iterative repair

When the reviewer requests changes, the runner passes only the bounded **structured findings as explicitly untrusted data** to the configured worker; the worker then executes in the same disposable workspace and test checks run again. The reviewer gets a fresh process and current workspace fingerprint on every round, but no worker narrative. Default review-round cap is **three**.

- An unsuccessful reviewer process, invalid JSON or contradictory source identity stops immediately instead of pointlessly repeating the same reviewer.
- A `blocked` review requires human investigation.
- Without a configured worker, `changes_requested` stops rather than burning extra reviewer tokens.
- Running out of rounds leaves `changes-requested`, not approval.
- Unintegrated worker edits leave `implementation-not-integrated` even if the last reviewer claimed approval and candidate tests returned zero.

## Durable recovery without stale-receipt reuse

For every opted-in `pipeline` execution, freview creates an atomic `checkpoint.json` in the **explicitly authorized scratch directory's run folder**. It records source SHA, first/current workspace digests, cycle, stage exit statuses and log artifact paths; raw prompts and credentials are not copied into the checkpoint.

Example to inspect a recovered run **without executing anything**:

```sh
python3 -I /path/to/freview/skills/freview/scripts/ops.py inspect-checkpoint \
  --checkpoint /approved/external/scratch/freview-ops-XXXX/checkpoint.json
```

The inspector rejects oversized inputs, symlinks, malformed metadata, forged `attested` fields and unknown stage entries. This record is **untrusted metadata, not a signed attestation**. `inspect-checkpoint` intentionally does not resume or skip tests. To continue from an interrupted run, manually inspect logs and workspace, create/reconcile a new immutable candidate commit if needed, and re-run authorized checks against that new exact source identity.

## Limitations / external acceptance

The unit tests use fake local reviewer and worker subprocesses. Real Claude, Codex and OpenCode provider CLIs may require explicit non-interactive JSON wrappers or adapters. No provider has been invoked in this tranche; no automatic provider installation, account login, token forwarding, mutation tooling, branch merge or release is implied.

GitHub Actions green establishes only that the tested **freview helper code** passes the deterministic test suite at that exact commit. It does not prove that an external agent actually read the source or that a malicious program was contained by an OS sandbox. Treat candidate worktrees as trusted code unless separately isolated.
