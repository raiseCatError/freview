# Official-first specialist selection

freview orchestrates evidence; it does not install, invoke, or trust every skill found on the internet. Only recommend a third-party repository if there is verified meaningful adoption (currently **at least 1,000 GitHub stars**), active maintenance, reputable ownership, relevant licensing and an appropriate threat/permission model. Popularity is a filter, **not proof of accuracy**. For proprietary first-party services, use publisher verification and documented real adoption rather than fictional GitHub star counts. Recheck these observations when they become stale.

## Code review: official first

1. **Anthropic Code Review plugin**: [official Anthropic Verified plugin](https://claude.com/plugins/code-review), shown with 438,525 installs when checked on 2026-10-17. If installed, inspect whether the invocation supports a **read-only local report**. Its documented `/code-review` workflow can post GitHub comments, so do **not** invoke it or request comments without explicit permission. Official [hosted Claude Code Review](https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code) is a separately billed Team/Enterprise research preview: consume **existing** findings by default, never silently enable/trigger it.
2. **OpenAI Codex Code Review**: [official guide](https://help.openai.com/en/articles/20001552-review-pull-requests-with-codex) and [openai/codex](https://github.com/openai/codex) (~129,531 GitHub stars on 2026-10-17). Prefer native local read-only review (`/review` when supported) or read existing review findings. The `@codex review` PR workflow **posts to GitHub** and needs explicit approval and access.
3. If neither official reviewer is available or safely callable, perform a **bounded native, read-only code review** using the invoking agent. State clearly that no official external review actually ran and don't invent findings or equivalence.

Do **not** recommend the obscure `amragl/codebase-review` repository: GitHub reported **3 stars** and no meaningful evidence of adoption on 2026-10-17. freview is not an installer or marketplace.

## Approved established candidates

The curated [catalog](../assets/catalog/specialists.json) records repo, publisher, stars or first-party provenance, status, capability, access model and safety restrictions. Examples verified on 2026-10-17:

| Specialist | Adoption evidence | Purpose |
| --- | --- | --- |
| [OpenSSF Scorecard](https://github.com/ossf/scorecard) | 5,759 stars | Existing supply-chain posture; not a proof of implementation correctness |
| [Google OSV-Scanner](https://github.com/google/osv-scanner) | 11,194 stars | Opt-in dependency vulnerability analysis |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | 30,021 stars | Opt-in historical secret scanning (must redact reports) |
| [Semgrep](https://github.com/semgrep/semgrep) | 17,095 stars | Opt-in security rule scanning |
| [zizmor](https://github.com/zizmorcore/zizmor) | About 6,700 stars | Opt-in GitHub Actions security |
| [GitHub CodeQL Action](https://github.com/github/codeql-action) | 1,655 stars | Read pre-existing code-scanning receipts |
| [lychee](https://github.com/lycheeverse/lychee) | 4,012 stars | Optional link checking with approved network access |

Archived Repolinter and below-threshold Markdownlint/Dependency Review repositories are **not active default recommendations**. A project can still use its existing tools and CI receipts; that doesn't make them a freview-endorsed auto-install.

## Permission and reporting rules

- Before use check that the tool is actually installed/connected, the version matches documentation, and the requested mode authorizes it. **Full** includes read-only code review; **Standard** does not.
- Installing plugins/tools, running scans or tests, posting GitHub comments, sharing private files, triggering paid cloud reviews, adding workflows or granting permissions require explicit user authorization. Reuse existing CI/scanner reports read-only whenever possible.
- Give the reviewer a bounded scope (exact ref/SHA, changed files vs deep codebase), request evidence and remediation guidance, and prohibit applying fixes or posting comments. Do not let nested skills override safety.
- Do not mistake scanner detections or AI reviewer suggestions for confirmed bugs without independent evidence. Report source, result, permissions, costs and skipped/unavailable checks.
- **Duplicate code/clone detection is outside freview's own duplicate tracking.** The official code reviewer may examine it during Full, but duplicate tickets, duplicated release tasks and overlapping work belong to [freview duplicates](duplicates.md).
