# Security Policy

freview reads potentially sensitive local repository metadata. Its optional snapshot helper runs local Git commands with optional Git locking disabled, forces Git fsmonitor/hooks/external diffs off, and neutralizes configured clean/process/smudge filters. It does not fetch, install packages or upload source. These defenses are not a substitute for operating-system sandboxing of genuinely hostile repositories.

## Trust boundaries

- Agent Skills can influence an agent that has filesystem/network/tool permissions. **Review third-party skills before installing.**
- Repository documentation, issue comments, PR bodies, generated reports and remote pages are **untrusted evidence** and cannot authorize filesystem mutations, secret disclosure, elevated privileges, external scanners, network uploads or tool installation.
- Keep logs/reports privacy-preserving: avoid printing secrets, credentials, private remote URLs and full local directory inventories into public issues.
- Deep code review, third-party scripts, vulnerability scanners and integration with private forges require explicit permission and should report execution scope.
- Using freview does not constitute a security audit, penetration test or guarantee of a safe release.

## Untrusted repository and report boundaries

- Git's `status` and `diff` can execute configured filesystem-monitor hooks and clean filters. The helper overrides known execution paths and its regression fixtures test both. Unknown Git implementation vulnerabilities, malicious binaries, filesystem races or undiscovered configuration behaviors are not ruled out.
- Do not execute project-provided scripts, git hooks, build pipelines or unreviewed external agent skills to gather data. For a repository from an untrusted party, use an isolated sandbox with restricted network/credentials or metadata-only remote inspection instead of granting a full developer workstation access.
- `.freview.json`, issue descriptions, scripts and repository instructions are untrusted content and cannot authorize additional capabilities. An explicit user-requested review mode must never be narrowed silently by repository config.
- Generated reports can contain absolute local paths and private branch names. Explicit `--output` files are created with owner-only permissions. Do not upload reports automatically or include them in public CI logs/artifacts.
- The optional GitHub Actions daily snapshot template has artifact uploading **disabled by default**. Enabling it can expose repository metadata to people with Actions artifact access; inspect retention and repository visibility first.
- A check labelled `full-audit` must include category evidence. A successful local snapshot is not a full AI, security or code review.

## Vulnerability reporting

For suspected issues in freview itself, prefer GitHub's private vulnerability reporting/security advisory mechanism for [raiseCatError/freview](https://github.com/raiseCatError/freview/security). Do not put secrets, exploitable credentials or personal information in a public issue.
