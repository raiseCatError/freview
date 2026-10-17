---
name: Bug report
about: Report an incorrect audit, broken helper, or agent skill activation problem
title: "bug: "
---

## What happened?
Describe the observable failure without including private source, local usernames, tokens, or complete agent transcripts.

## Expected behavior
What classification, command behavior, or evidence should freview have produced?

## Actual behavior
What did it produce? Distinguish a helper's `local-snapshot` from a complete agent review.

## Reproduction
1. Repo type / minimal **sanitized or disposable** fixture:
2. Commands or native skill invocation (omit credentials and private paths):
3. Inputs and expected versus actual results:

## Environment and evidence
- freview commit or installed skill revision:
- Agent and version (if applicable):
- Native skill discovery/invocation observed? yes / no / unverified
- OS, Python and Git versions (if relevant):
- Target Git ref/HEAD; staged, unstaged, untracked state (sanitized):
- CI run URL and its **exact** checked SHA, if applicable:
- Local execution versus prior/hosted evidence:

## Safety and scope
What was not checked? Did the test create any files or require permission? Never upload private audit reports, full local paths, secrets, or unreviewed logs. For a possible vulnerability, use [private reporting guidance](../../SECURITY.md), not a public issue.
