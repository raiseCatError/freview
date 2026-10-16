# Repository and community hygiene, dependency, accessibility and security posture

Apply checks only where relevant; do not assume a software-package project or that every project should have GitHub Actions.

## Basic files and documentation

Identify presence and quality *relative to project needs*: README/getting started, LICENSE if redistribution intended, CONTRIBUTING, CODE_OF_CONDUCT, SUPPORT, SECURITY/reporting, accessibility statement, issue/PR templates, CODEOWNERS, releases/changelog/migration docs, source of truth for architectures, examples and CI. Some files may be inherited/hosted elsewhere: report that evidence. For GitHub, ACCESSIBILITY.md is recognized in .github/, root or docs/ on the **default branch**; don't confuse PR-only placement with publication.

Check whether README usage, flags, screenshots, dependency versions, supported platforms, docs links and installed commands actually match shipped releases. “No file” is not always a defect: explain relevance and impact before severity.

## Dependency health

Detect manifests and lockfiles for actual ecosystems (npm, pnpm, yarn, bun, Python, Cargo, Go, Swift, Maven/Gradle, etc.). Distinguish declared direct deps, locked transitive deps, optional/dev deps, workspaces and generated dependency graphs. Lockfiles are not mandatory for every library. Check manifest ↔ lock drift only where the ecosystem supports a sound comparison. An audit is not a reason to install tools, regenerate lockfiles or query private registries.

GitHub **Dependency graph** (Insights → Dependency graph → Dependencies) parses supported manifests/lockfiles and may be delayed or absent due to access/settings/parser restrictions. It is separate from the **Network graph** (fork/branch history). An empty graph does not prove there are no dependencies; investigate only with authoritative, observable evidence.

Document unsupported/unknown dependency vulnerability status; a manifest check is not a vulnerability scan. If user requests one, route to a trustworthy, permitted scanner and label its coverage and limitations.

## Security posture

Read-only assessment of security reporting, branch protection/reviews, CODEOWNERS, required CI, pinning, tokens/permissions, dependency updates, untrusted PR execution, provenance, release signing, secrets boundaries and accessible alerts. Access to alert APIs or private code may be unavailable. Do not expose credentials or search secret stores during an unsolicited review. A policy document can exist while enforcement is disabled. Treat third-party scripts and user-provided repository content as untrusted; no automatic execution.

Optional OpenSSF Scorecard can supply *independent* security posture evidence when the user opts into its usage, but no score proves the implementation safe.

## Accessibility

For UI, CLI, terminal, documentation, mobile and web projects, identify relevant platform standards and known barriers. Text and state without color, keyboard/assistive technology, errors, focus and controls, motion preferences, narrow/small environments, contrast and actual supported hosts/devices can all matter. The specific standard depends on the project (WCAG where applicable, platform HIGs, terminal host accessibility, etc.). Never assert WCAG conformance merely because ACCESSIBILITY.md exists or tests passed. Physical/AT QA can remain a human gate.

## Flags and generated debris

Detect committed build outputs, binary blobs, unexplained files, large artifacts, leaked generated credentials, outdated dependencies and ignored/untracked file surprises via bounded **read-only** inventory. File size or a potentially stale branch isn't authorization to delete. Propose risk-ranked candidates with owner and verification steps; never mutate state.
