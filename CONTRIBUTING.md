# Contributing to freview

Thanks for helping build a vendor-neutral, adaptable repository-review skill.

## Principles

- The default run is **read-only**, evidence-first, resource-bounded and permission-aware.
- Different repositories need different policies. No hardcoded branch names, stack assumptions or release conventions.
- A checker must distinguish `not verified` from `failed` and `not applicable`.
- A specialist tool or skill may be *recommended*, but must not be installed, executed or granted access without appropriate explicit authorization.
- No hidden deletion, branch pruning, network side effects, dependency installation or mutation of issues/PRs.
- Avoid implying unsupported agent compatibility. Document the version and test environment of new installation instructions.

## Local verification

The optional helper requires Python 3 and Git. The test suite is Python standard library only:

```sh
python3 -m unittest discover -s tests -v
```

Tests create temporary Git repositories and must use a safe scratch location; obey your host's external storage policy and avoid running heavy parallel suites.

## Proposing improvements

Use the [bug-report template](.github/ISSUE_TEMPLATE/bug_report.md) for incorrect audits, unsafe behavior or activation failures, and the [feature-request template](.github/ISSUE_TEMPLATE/feature_request.md) for proposed coverage. Pull requests should use the [review checklist](.github/pull_request_template.md). Never submit private working-tree inventories or raw reports to public issues.

Open an issue explaining which audit coverage is missing, why it affects real users, and how a reproducible fixture can validate the proposed detection. Submit a pull request with scope, tests/evidence, the desired classification and its false-positive limits. Do not paste private source, credentials or terminal history into public issues.

The skill should remain compact. Add focused, linked reference files rather than one giant repeated system prompt. Keep the report usable by people, with a transparent list of what the agent could not observe.
