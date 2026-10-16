# Daily automation and scheduled snapshots

**Standard is the daily mode:** Git, open issues and PRs, release/check status, basic implementation discrepancies, docs and dependency hygiene; **never deep code-quality review or a vulnerability scanner** unless specifically added to this invocation.

A human can run `freview standard` daily, or create a ChatGPT/agent scheduler where available to run the actual full agent-assisted review. Do not pretend the tool is a daemon, trigger cron itself, or perform background work.

## GitHub Actions template

The opt-in [daily snapshot template](../../../templates/github-actions/freview-daily.yml) illustrates a scheduled non-AI metadata check. It runs Python/Git against the checked-out repository, exports a JSON **local snapshot**, and stores it as a short-lived private-to-repo Actions artifact where GitHub permits. It does NOT automatically enumerate hosted issues, perform deep source review, invoke paid AI models or publish a security verdict.

Users must **copy and inspect** the template into their target project's `.github/workflows/`, choose permissions/retention, and ensure the skill's helper exists at the configured path. Nothing is enabled by installing the freview skill. Use a pinned release or vendored reviewed helper rather than downloading mutable `main` scripts with curl in every run.

Never automatically add a workflow to a consumer project. A truly scheduled **agent-assisted** daily review is a separate opt-in integration requiring provider credentials, project permissions and privacy review; no such hosted service is provided by freview v0.1.

## Comparable reports

JSON reports follow [report schema](../../../schemas/freview-report.schema.json). The optional CLI emits `report_kind=local-snapshot` with explicit gaps. The agent may produce a more complete `partial-audit` or `full-audit` only after actually investigating matching categories, and may compare it with a supplied prior report to show meaningful deltas. Don't invent history or use the date of a workflow run as evidence of an AI review.

Avoid persisting reports into version control by default, especially if they include user paths or private branch metadata. On developer laptops, obey the user's scratch disk policy; writing an explicit `--output` file is a user-authorized operation, not automatic hygiene cleanup.
