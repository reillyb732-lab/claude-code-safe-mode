"""Install (or remove) Safe Mode in your Claude Code settings.

    python install.py            # install
    python install.py --remove   # uninstall

Adds the Safe Mode hook and deny rules to ~/.claude/settings.json without touching
your other settings (a backup is saved first), and adds the /safety-check command.
"""
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAUDE = Path.home() / ".claude"
SETTINGS = CLAUDE / "settings.json"
SKILL_DIR = CLAUDE / "skills" / "safety-check"
MATCHER = "Bash|PowerShell|Read|Edit|Write|NotebookEdit|Glob|Grep"
DENY = ["Read(~/.ssh/**)", "Edit(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.gnupg/**)"]
MARK = "safe_mode.py"


def hook_command():
    py = Path(sys.executable).as_posix()
    return f'"{py}" "{(HERE / "safe_mode.py").as_posix()}"'


def load():
    if not SETTINGS.exists():
        return {}
    text = SETTINGS.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else {}


def strip_hook(settings):
    groups = settings.get("hooks", {}).get("PreToolUse", [])
    for g in groups:
        g["hooks"] = [h for h in g.get("hooks", []) if MARK not in h.get("command", "")]
    groups[:] = [g for g in groups if g["hooks"]]


def main():
    remove = "--remove" in sys.argv
    try:
        settings = load()
    except ValueError:
        sys.exit(f"Your {SETTINGS} isn't valid JSON, so I won't touch it. Fix it (or ask Claude to) and run this again.")
    if SETTINGS.exists():
        backup = SETTINGS.with_name(f"settings.backup-{time.strftime('%Y%m%d-%H%M%S')}.json")
        shutil.copy2(SETTINGS, backup)
        print(f"Backed up your settings to {backup.name}")

    strip_hook(settings)  # never add the hook twice
    perms = settings.setdefault("permissions", {})
    deny = perms.setdefault("deny", [])
    if remove:
        perms["deny"] = [r for r in deny if r not in DENY]
        shutil.rmtree(SKILL_DIR, ignore_errors=True)
    else:
        settings.setdefault("hooks", {}).setdefault("PreToolUse", []).append(
            {"matcher": MATCHER, "hooks": [{"type": "command", "command": hook_command()}]})
        deny += [r for r in DENY if r not in deny]
        SKILL_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / "safety-check" / "SKILL.md", SKILL_DIR / "SKILL.md")
    if not perms.get("deny"):
        perms.pop("deny", None)
    if not perms:
        settings.pop("permissions", None)
    if not settings.get("hooks", {}).get("PreToolUse"):
        settings.get("hooks", {}).pop("PreToolUse", None)
    if settings.get("hooks") == {}:
        settings.pop("hooks")

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print("Safe Mode removed." if remove else
          "Safe Mode installed. Restart Claude Code, then type /safety-check to see your protection report.")


if __name__ == "__main__":
    main()
