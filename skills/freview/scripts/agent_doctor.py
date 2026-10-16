#!/usr/bin/env python3
"""freview agent discovery doctor. Zero model calls; no shell execution or writes."""
import argparse
import json
import os
from pathlib import Path
import stat
import re
import shutil

AGENT_NAMES = {"claude": "claude", "codex": "codex", "opencode": "opencode",
               "agy": "agy", "antigravity": "agy"}
DEFAULT_NAMES = ("claude", "codex", "opencode", "agy")
ENV_BY_AGENT = {"claude": "CLAUDE_CONFIG_DIR", "codex": "CODEX_HOME",
                "opencode": "OPENCODE_CONFIG_DIR"}
NAME = r"[a-zA-Z][a-zA-Z0-9_-]{0,70}"
ALIAS = re.compile(r"^\s*alias\s+(" + NAME + r")\s*=\s*(.*)$")
FUNCTION = re.compile(r"^\s*(?:function\s+)?(" + NAME + r")\s*(?:\(\s*\))?\s*\{\s*$")
ENV_ASSIGN = re.compile(r"(?<![\w])(?:export\s+)?(CLAUDE_CONFIG_DIR|OPENCODE_CONFIG_DIR|CODEX_HOME)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s;]+))")
FISH_ASSIGN = re.compile(r"\bset\s+-(?:gx|lx|xg|xl)\s+(CLAUDE_CONFIG_DIR|OPENCODE_CONFIG_DIR|CODEX_HOME)\s+(?:\"([^\"]*)\"|'([^']*)'|([^\s;]+))")
MAX_CONFIG_BYTES = 128 * 1024
MAX_DEFINITIONS = 128
BUNDLE_REQUIRED = (
    "SKILL.md", "scripts/repo_snapshot.py", "scripts/review.py",
    "scripts/report_tools.py", "scripts/duplicates.py", "scripts/agent_doctor.py",
    "assets/schemas/freview-config.schema.json",
    "assets/schemas/freview-report.schema.json",
    "assets/catalog/specialists.json", "assets/templates/github-actions/freview-daily.yml",
    "references/agent-discovery.md", "references/automation.md",
    "references/configuration.md", "references/delivery.md",
    "references/discovery.md", "references/duplicates.md", "references/git.md",
    "references/hygiene.md", "references/modes.md", "references/remediation.md",
    "references/specialists.md", "references/report.md",
)


def infer_agent(name, body):
    lower = name.lower()
    for key, kind in (("opencode", "opencode"), ("claude", "claude"),
                      ("codex", "codex"), ("agy", "agy")):
        if re.search(r"(?<![\w-])" + key + r"(?![\w-])", body):
            return kind
    if lower.startswith("claude"):
        return "claude"
    if lower.startswith("opencode"):
        return "opencode"
    if lower.startswith("codex"):
        return "codex"
    if lower.startswith(("agy", "antigravity")):
        return "agy"
    return None


def parse_profile_path(raw, home):
    """Expand literal $HOME and ~ only; never evaluate shell syntax."""
    if not raw or "\n" in raw or "\r" in raw or "\x60" in raw or "$(" in raw:
        return None
    s = raw.replace(chr(36) + "{HOME}", str(home)).replace("$HOME", str(home))
    if s == "~":
        s = str(home)
    elif s.startswith("~/"):
        s = str(home / s[2:])
    if "$" in s or "\\" in s or not s.startswith("/") or len(s) > 2048:
        return None
    return Path(os.path.normpath(s))


def extract_profiles(body, home):
    result = {}
    for match in (*ENV_ASSIGN.finditer(body), *FISH_ASSIGN.finditer(body)):
        var = match.group(1)
        value = next((s for s in match.groups()[1:] if s is not None), None)
        result[var] = parse_profile_path(value, home)
    return result


def read_shell_file(path):
    # Treat shell files as untrusted content. No sourcing or symlink following.
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_CONFIG_BYTES:
                return None
            raw = stream.read(MAX_CONFIG_BYTES + 1)
        return raw.decode("utf-8", "replace") if len(raw) <= MAX_CONFIG_BYTES else None
    except OSError:
        return None


def scan_definitions(contents, source, home):
    """Extract agent aliases/functions; never return raw shell command bodies."""
    found = []
    lines = contents.splitlines()
    i = 0
    while i < len(lines) and len(found) < MAX_DEFINITIONS:
        line = lines[i]
        match = ALIAS.match(line)
        if match:
            name, body = match.groups()
            kind = infer_agent(name, body)
            if kind:
                found.append({"command": name, "agent": kind, "kind": "alias",
                              "source": str(source), "profiles": extract_profiles(body, home)})
            i += 1
            continue
        match = FUNCTION.match(line)
        if match:
            name = match.group(1)
            body_lines = []
            for extra in lines[i + 1:i + 33]:
                if extra.strip() == "}":
                    break
                body_lines.append(extra)
            body = "\n".join(body_lines)
            kind = infer_agent(name, body)
            if kind:
                found.append({"command": name, "agent": kind, "kind": "function",
                              "source": str(source), "profiles": extract_profiles(body, home)})
            i += 1
            continue
        i += 1
    return found


def referenced_assets(root):
    """Statically discover bundled links in SKILL.md; never execute content."""
    required = set(BUNDLE_REQUIRED)
    skill = root / "SKILL.md"
    try:
        if skill.stat().st_size <= 256 * 1024:
            body = skill.read_text(encoding="utf-8")
            for link in re.findall(r"\]\(([^)]+)\)", body):
                target = link.split("#", 1)[0]
                if target.startswith(("references/", "assets/", "scripts/")) and (
                        ".." not in Path(target).parts and not Path(target).is_absolute()):
                    required.add(target)
    except (OSError, UnicodeError):
        pass
    return sorted(required)


def skill_path_state(path):
    try:
        if path.is_symlink() and not path.exists():
            return "broken-symlink"
        if (path / "SKILL.md").is_file():
            return "present"
        return "missing"
    except OSError:
        return "unknown"


def skill_locations(agent, home, workspace, overrides):
    common = home / ".agents/skills/freview"
    project = workspace / ".agents/skills/freview" if workspace else None
    paths = []
    if agent == "claude":
        profile = overrides.get("CLAUDE_CONFIG_DIR", home / ".claude")
        paths = [profile / "skills/freview"] if profile is not None else []
        if workspace:
            paths.append(workspace / ".claude/skills/freview")
    elif agent == "codex":
        config_home = overrides.get("CODEX_HOME", home / ".codex")
        paths = ([config_home / "skills/freview"] if config_home is not None else []) + [common]
    elif agent == "opencode":
        paths = [common, home / ".config/opencode/skills/freview",
                 home / ".claude/skills/freview"]
        if overrides.get("OPENCODE_CONFIG_DIR"):
            paths.insert(0, overrides["OPENCODE_CONFIG_DIR"] / "skills/freview")
        if workspace:
            paths.extend([workspace / ".opencode/skills/freview",
                          workspace / ".claude/skills/freview"])
    elif agent == "agy":
        paths = [home / ".gemini/antigravity-cli/skills/freview",
                 home / ".gemini/config/skills/freview",
                 home / ".gemini/skills/freview"]
    if project and agent in ("codex", "opencode", "agy"):
        paths.append(project)
    unique = []
    for path in paths:
        if path not in unique:
            unique.append(path)
    return [{"path": str(path), "status": skill_path_state(path)} for path in unique]


def inspect(home, workspace=None, extra_files=(), shell_scan=True):
    home = Path(home)
    workspace = Path(workspace) if workspace else None
    shell_files = [home / name for name in (
        ".zshrc", ".zprofile", ".zsh_aliases", ".bashrc", ".bash_profile",
        ".aliases", ".config/zsh/.zshrc", ".config/zsh/aliases.zsh",
        ".config/zsh/aliases", ".config/fish/config.fish")]
    shell_files += [Path(path) for path in extra_files]
    definitions = []
    seen_source = set()
    if shell_scan:
        for path in shell_files:
            if str(path) in seen_source:
                continue
            seen_source.add(str(path))
            content = read_shell_file(path)
            if content is not None:
                definitions.extend(scan_definitions(content, path, home))
    commands = [{"command": name, "agent": kind, "kind": "default", "source": "PATH",
                 "profiles": {}} for name, kind in AGENT_NAMES.items() if name in DEFAULT_NAMES]
    commands.extend(definitions)
    output = []
    for cmd in commands:
        overrides = cmd["profiles"]
        if cmd["kind"] == "default":
            var = ENV_BY_AGENT.get(cmd["agent"])
            if var and os.environ.get(var):
                overrides = {var: parse_profile_path(os.environ[var], home)}
        locations = skill_locations(cmd["agent"], home, workspace, overrides)
        for item in locations:
            item["bundle"] = "not-checked"
            if item["status"] == "present":
                root = Path(item["path"])
                missing = [asset for asset in referenced_assets(root)
                           if not (root / asset).is_file()]
                item["bundle"] = "incomplete" if missing else "complete"
                item["missing_assets"] = missing
        active_var = ENV_BY_AGENT.get(cmd["agent"])
        resolution = "not-applicable"
        if active_var:
            if active_var in overrides:
                resolution = "resolved" if overrides[active_var] else "dynamic-or-unresolved"
            else:
                resolution = "default-or-unobserved"
        output.append({"command": cmd["command"], "agent": cmd["agent"],
                       "definition": cmd["kind"], "definition_file": cmd["source"],
                       "profile_resolution": resolution,
                       "profile_path": str(overrides[active_var]) if active_var in overrides and overrides[active_var] else None,
                       "executable": shutil.which(cmd["agent"]) if cmd["kind"] == "default" else None,
                       "underlying_binary_guess": (shutil.which(cmd["agent"])
                            if cmd["kind"] != "default" else None),
                       "skill_locations": locations,
                       "freview_visible_on_disk": any(x["status"] == "present" for x in locations),
                       "bundle_complete": any(x.get("bundle") == "complete" for x in locations),
                       "activation_confirmed": False})
    return {"kind": "freview-agent-doctor/1", "inspection": "read-only; static only",
            "warning": "Shell files scanned, never sourced. Dynamic aliases/functions and agent activation require separate verification.",
            "commands": output}


def markdown(data):
    lines = ["# freview agent installation doctor", "",
             "Static discovery only. No shell configs executed, no model calls, no files changed.", "",
             "| Command | Agent | Definition | Profile | freview | Bundle |",
             "|---|---|---|---|---|---|"]
    for cmd in data["commands"]:
        def safe(s):
            return str(s or "—").replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(map(safe, (
            cmd["command"], cmd["agent"], cmd["definition"],
            cmd["profile_path"] or cmd["profile_resolution"],
            "yes" if cmd["freview_visible_on_disk"] else "no",
            "complete" if cmd["bundle_complete"] else "missing/incomplete"))) + " |")
    lines += ["", "A visible skill file is **not** proof of agent activation.",
              "Run the agent's native skill list/reload UI to confirm it loads."]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="No-token/read-only agent alias/profile/skill discovery")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--workspace", help="project folder to inspect; no traversal")
    parser.add_argument("--shell-config", action="append", default=[], help="additional shell rc file to inspect (no execution)")
    parser.add_argument("--no-shell-scan", action="store_true", help="skip reading shell startup files")
    args = parser.parse_args(argv)
    result = inspect(Path.home(), args.workspace, args.shell_config, not args.no_shell_scan)
    print(json.dumps(result, indent=2) if args.format == "json" else markdown(result))


if __name__ == "__main__":
    main()
