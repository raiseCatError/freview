# freview integration verification — 2026-10-17

**Verification classification:** automated exact-head integration verified; **physical multi-agent acceptance outstanding**.

## Integrated baseline

The previously independent changes were merged sequentially into `main`, without changing the original freview-on-freview historical [draft PR #8](https://github.com/raiseCatError/freview/pull/8).

| Source PR | Merge commit | Functionality |
| --- | --- | --- |
| [#9 — local-first review](https://github.com/raiseCatError/freview/pull/9) | `870a96c17506e56b0896778e0124927c54227b8b` | Bounded staged/unstaged/untracked inventory, unborn repos, opt-in worktree statuses, provisional tracking, identity guard, local/cloud policy |
| [#10 — duplicate work](https://github.com/raiseCatError/freview/pull/10) | `434a0ef0e55ad9ca8abc154c2b7ac1bbfc8948e5` | `Refs #N` relations, bounded stdin, pair budget, terminal-safe candidate text |
| [#11 — trust and diagnostics](https://github.com/raiseCatError/freview/pull/11) | `abcab7d62affc61ba4aeb0f7c40008e64a7acd30` | Honest report comparisons, bounded report reads, UTC enforcement, installation doctor, advisory publication lint |
| [#12 — independent audit archive](https://github.com/raiseCatError/freview/pull/12) | `3870b786deb8b7112b72bdac54dfb9150e250fab` | Privacy-conscious comparison of independent source review and NMSh field test |

**Exact integrated HEAD assessed:** `3870b786deb8b7112b72bdac54dfb9150e250fab`.

## Automated verification

- [GitHub Actions on integrated SHA](https://github.com/raiseCatError/freview/actions/runs/38976562915) — **success**, exact `3870b786`.
- **Ubuntu latest:** 93/93 Python tests passed (7.486s). `python3 -m py_compile`, standalone snapshot, isolated quick/standard/full local CLI modes, existing UTC self-audit schema validation, agent doctor smoke and `git diff --check` all passed.
- **macOS latest:** 93/93 Python tests passed (34.655s), same workflow steps.
- CI uses the workflow's configured Python **3.11** on both operating systems. The earlier AGY local run used a separately reported Python 3.14.8. Do not combine those environments or claim a CI Python-version matrix.
- Green tests are evidence only for their configured assertions; they do **not** prove arbitrary-untrusted-repository safety, runtime skill activation, or a fully completed AI audit.

## Independent experiment

- A prior AGY Full-mode session operated through **manual SKILL.md instructions** because native freview prompt injection was not observed in that AGY workspace. Its local helper execution and agent source review remain useful evidence, but its **native activation is not verified**.
- The private NMSh field test highlighted real gaps in non-closing issue references and user-appropriate Git bases; its specific PR #357 / issue #355 duplicate claim was not independently reproduced. Changes avoid enshrining unverified claims as regressions.
- [Independent cross-review](2026-10-17-independent-cross-review.md) remains the source-level / evidence-reconciliation record, not a certification of user's local Mac state.
- The four original NMSh files remain private and are not copied into this repository because they can contain workstation paths, branch names and unpublished development details.

## Outstanding release gates

1. **Physical native activation**: in fresh actual client sessions (AGY 1.4.0 or current, Claude Code, Codex, OpenCode), prove installed assets → native skill list → native freview invocation → helper smoke → actual Full agent review. See [repeatable acceptance checklist](../testing/agent-activation-acceptance.md).
2. **Local working-tree depth**: the helper inventories bounded paths and statuses, while Full agent review must examine relevant staged + unstaged diff bodies and untracked source safely. A `local-snapshot` is not a code review.
3. **Publication evidence**: tracking refs are cached until separately corroborated by authoritative forge data; `ahead` is provisional, not a verified unpushed commit. Worktrees may change concurrently.
4. **Privacy/trust**: `--check-public` is advisory and cannot guarantee a safe report; structured source/evidence receipt authentication and fuller redaction remain pending.
5. **Resource behavior**: branch divergence budget is implemented, but end-to-end Git process and output-byte budgets need adversarial large-repository tests.
6. **Independent final review**: run freview-on-freview in a fresh session pinned to its **actual merged skill version**, compare against PR #8 and this receipt; record missing evidence rather than asserting full completion.

## Preservation and change policy

Do not rewrite the original audit to make it seem it tested this new integrated SHA. Maintain an additive evidence history. These improvements were integrated into freview, **not** into notMyShell. No automatic releases/tags or mutations to NMSh are authorized by this receipt.
