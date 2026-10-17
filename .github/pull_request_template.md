## Summary
What changed and why? Link the issue or audit finding, if one exists.

## Scope and evidence
- Target/base branch and exact tested HEAD:
- Files/components and behavior changed:
- Related PRs or duplicate-work check:
- Implementation status: proposed / implemented / integrated / verified
- What remains unverified or intentionally deferred:

## Safety / trust boundaries
- [ ] Read-only defaults remain intact; no unauthorized fetch, install, hook execution, source upload, branch deletion, or issue mutation
- [ ] Local-first states (staged, unstaged, untracked, worktrees, cached upstream) and remote evidence are distinguished when applicable
- [ ] Untrusted file/forge inputs have bounded reads and safe output; private paths and secrets are not published
- [ ] Any user-visible permission or security behavior changes are documented

## Verification
- [ ] Focused tests or reproduction fixture described below
- [ ] Existing Ubuntu and macOS checks verified on the **PR head SHA**
- [ ] No test-generated source checkout changes
- [ ] Documentation, examples, bundled skill assets and report schema considered
- [ ] Native agent / physical QA status reported honestly as PASS, FAIL, PARTIAL, or NOT OBSERVED

**Commands / CI run(s) / exact SHA(s):**

**Checks intentionally not run and why:**

## Release / cleanup
Does this require a release, manual acceptance, documentation change, or follow-up? No PR merge or green CI result alone proves a published release.
