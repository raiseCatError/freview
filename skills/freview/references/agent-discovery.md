# Agent skill/profile discovery — read-only

freview supports multi-account agent setups such as `claude-account1`, `claude-account2`, `opencode1` and `opencode2`. A global `~/.claude/skills/freview` is **not** proof that a Claude launcher using `CLAUDE_CONFIG_DIR` can load freview.

## Zero-model-token diagnostic

From a checked-out freview repository:

```sh
python3 skills/freview/scripts/agent_doctor.py --workspace "$PWD"
python3 skills/freview/scripts/agent_doctor.py --workspace "$PWD" --format json
```

Or from any installed freview skill directory:

```sh
python3 <installed-freview-skill>/scripts/agent_doctor.py --format markdown
```

No agent runs and no accounts are switched. It only inspects selected, bounded shell configuration files (`~/.zshrc`, `~/.zprofile`, `~/.bashrc`, common zsh aliases and fish config), and optional explicit additional files:

```sh
python3 skills/freview/scripts/agent_doctor.py --shell-config "$HOME/.config/my-agent-aliases.zsh"
python3 skills/freview/scripts/agent_doctor.py --no-shell-scan
```

It recognizes simple bash/zsh aliases and functions and extracts **only** `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and `OPENCODE_CONFIG_DIR` path assignments. It expands only literal `~` and `$HOME`. **It never sources or runs shell startup code**, executes wrappers, starts agents, contacts the network, changes symlinks, touches account authentication files or writes a report. It does not print raw alias/function bodies or unrelated environment variables.

It reports each recognized launcher's definition kind/source, safely resolved (or unresolved) profile root, skill paths, broken symlinks, and whether the bundled `SKILL.md`, references, helpers and schemas appear complete.

## Crucial limitations

- A shell alias or function may be loaded dynamically through `source`, an installed plugin, `eval`, or interactive session state. Static parsing **cannot** prove its effective runtime definition. Supply the containing shell file with `--shell-config`; otherwise label it unobserved. Don't blindly invoke `zsh -ic` or `source ~/.zshrc` just to detect aliases: shell initialization can execute arbitrary commands.
- Alias definitions may be complex (environment variables set in other functions, runtime profile switchers, command substitution). Mark such paths `dynamic-or-unresolved`, never evaluate shell code.
- Claude Code uses `CLAUDE_CONFIG_DIR` as its profile directory. Global user skills should be checked under **that profile's** `skills/` directory, not only under the default `~/.claude/skills/`. A project-local `.claude/skills/` can also apply. <https://code.claude.com/docs/en/env-vars>
- OpenCode discovers `~/.agents/skills/` as well as `~/.config/opencode/skills/` and Claude-compatible locations. An OpenCode alias can still work when it uses a custom `OPENCODE_CONFIG_DIR`, because shared/global skill directories remain visible. <https://docs.opencode.ai/docs/skills/> and <https://docs.opencode.ai/docs/config/>
- Codex uses `CODEX_HOME` when customized; project-local `.agents/skills/` is supported. <https://developers.openai.com/blog/skills-agents-sdk>
- Antigravity CLI (`agy`) uses `~/.gemini/antigravity-cli/skills/` and project `.agents/skills/`. Other Antigravity surfaces may differ. <https://www.antigravity.google/docs/skills?tab=cli>
- The doctor performs a **static filesystem smoke test only**. `freview_visible_on_disk=true` and `bundle_complete=true` do not mean the actual agent loaded the skill. Check each agent's native skill discovery/reload UI for activation evidence.

## Remediation policy

A missing profile-specific skill should result in a **suggested target directory**, not automatic link creation or installation. Review actual alias/profile resolution and get permission before recommending explicit `ln -s` or other state changes. Never overwrite user files, inspect authentication credentials, follow untrusted shell-config symlinks, or modify existing installations as part of a review.

For multiple Claude account wrappers, report **each account separately** even if they share one binary. Treat OpenCode's default and custom profiles separately without claiming missing custom links are broken if the canonical global skill is present.

**Antigravity global-path nuance:** Documented global locations can include both `~/.gemini/antigravity-cli/skills/freview` and `~/.gemini/config/skills/freview`. The doctor checks both plus workspace `.agents/skills/freview`. Native prompt injection may still differ by AGY version, symlink behavior and startup; a present directory does not establish active skill loading. For aliases, `underlying_binary_guess` is a static PATH lookup, not proof of which executable a shell wrapper actually launches.
