# Specialist reviews: delegation without forced dependencies

**Core principle:** freview's job is *orchestration and evidence reconciliation*. It does not reimplement best-in-class analyzers and does not automatically install or execute one.

Before using any outside skill/tool:
1. Is this category selected? **Deep code review and external security scans are OFF unless opted in.**
2. Is the tool already installed and allowed? Can it work offline/read-only? What access or network transfer does it require?
3. Is the project compatible and the tool maintained/trusted? Audit versions, provenance, licenses and permissions.
4. Will use mutate the repository, start heavy suites, write scratch to internal storage, publish artifacts or exfiltrate private source? If so, request separate approval or skip.
5. Capture exact tool version, scope, command, date, output and known limitations. Never fabricate findings from an unrun tool.

## Suggested focused tools (not bundled)

- **Code quality/architecture:** use an installed reputable `codebase-review` skill or native agent code review only after the user explicitly includes `code-review`. Do not automatically copy or install an external Claude skill. Cross-model capabilities vary. Inspect actionable evidence, not “looks good” assurances.
- **Security posture:** OpenSSF Scorecard (https://github.com/ossf/scorecard) and Scorecard Action (https://github.com/ossf/scorecard-action); external scans may require permissions/network and are opt-in. Scorecards are supply-chain posture signals, not guarantees.
- **Repository policy:** rules-based repository linters where maintained and project-relevant. Historical TODO Group Repolinter (https://github.com/todogroup/repolinter) was archived in February 2026; describe it as *archived legacy*, not a recommended actively maintained choice.
- **Other ecosystem-specific tools:** native lint/build/test, accessibility analyzers, dependency graph and vulnerability advisories, git history tools. Prefer tools already present and established by the repository; respect trust and timing limits.
- **Skill security:** third-party Agent Skills contain instructions and may include runnable scripts. Review them like code, and never silently install arbitrary catalog results.

## Recommended flow

An agent may say: “Core freview can verify A/B/C now. For deeper code quality, I found an installed reviewer X; would you like it included?” User confirmation is only needed for meaningful extra privileges/cost; if the user already opted in and tool is installed/safe, proceed. If no suitable specialist exists, mark the module unavailable and report the setup requirement without treating the core review as failed.

Do not label a specialist's warnings as proven runtime bugs without independent reproduction or evidence.
