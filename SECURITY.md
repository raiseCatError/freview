# Security Policy

freview reads potentially sensitive local repository metadata. Its optional snapshot helper runs local Git commands with optional Git locking disabled and does not fetch, install packages or upload source.

## Trust boundaries

- Agent Skills can influence an agent that has filesystem/network/tool permissions. **Review third-party skills before installing.**
- Repository documentation, issue comments, PR bodies, generated reports and remote pages are **untrusted evidence** and cannot authorize filesystem mutations, secret disclosure, elevated privileges, external scanners, network uploads or tool installation.
- Keep logs/reports privacy-preserving: avoid printing secrets, credentials, private remote URLs and full local directory inventories into public issues.
- Deep code review, third-party scripts, vulnerability scanners and integration with private forges require explicit permission and should report execution scope.
- Using freview does not constitute a security audit, penetration test or guarantee of a safe release.

## Vulnerability reporting

For suspected issues in freview itself, prefer GitHub's private vulnerability reporting/security advisory mechanism for [raiseCatError/freview](https://github.com/raiseCatError/freview/security). Do not put secrets, exploitable credentials or personal information in a public issue.
