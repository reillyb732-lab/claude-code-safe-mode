"""Print a plain-English safety report for your Claude Code setup (used by /safety-check)."""
import json
import sys
import time
from pathlib import Path

HOME = Path.home()
CLAUDE = HOME / ".claude"
LOG = CLAUDE / "safe-mode" / "log.jsonl"


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    settings = load(CLAUDE / "settings.json")
    good, warn = [], []

    hooked = any("safe_mode.py" in h.get("command", "")
                 for g in settings.get("hooks", {}).get("PreToolUse", []) for h in g.get("hooks", []))
    (good if hooked else warn).append(
        "Safe Mode is on: risky commands need your OK, and your keys and browser passwords are blocked."
        if hooked else "Safe Mode's hook isn't installed. Run: python install.py")

    perms = settings.get("permissions", {})
    if perms.get("defaultMode") == "bypassPermissions" or settings.get("skipDangerousModePermissionPrompt"):
        warn.append("Claude is set to skip ALL permission prompts (bypass mode). Only use that in a throwaway folder.")
    broad = [r for r in perms.get("allow", []) if r in ("Bash", "Bash(*)", "PowerShell", "PowerShell(*)")
             or r.endswith(":*)") and r.split("(")[0] in ("Bash", "PowerShell") and len(r) < 16]
    if broad:
        warn.append(f"These 'always allow' rules let Claude run almost any command without asking: {', '.join(broad)}")
    if perms.get("deny"):
        good.append(f"{len(perms['deny'])} file rule(s) stop Claude from reading private folders.")

    exposed = [p for p in (".ssh", ".aws", ".gnupg") if (HOME / p).exists()]
    if exposed:
        good.append(f"Found private folders on this computer ({', '.join(exposed)}); "
                    + ("Safe Mode protects them." if hooked else "they are NOT protected yet."))

    week_ago = time.time() - 7 * 86400
    events = []
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("t", 0) >= week_ago:
                events.append(e)

    print("SAFE MODE REPORT\n")
    for g in good:
        print(f"  ✓ {g}")
    for w in warn:
        print(f"  ⚠ {w}")
    print(f"\nLast 7 days: {sum(e['decision'] == 'deny' for e in events)} blocked, "
          f"{sum(e['decision'] == 'ask' for e in events)} needed your OK")
    for e in events[-5:]:
        print(f"  - {time.strftime('%b %d %I:%M%p', time.localtime(e['t']))}  {e['decision'].upper():4}  {e['why']}")


if __name__ == "__main__":
    main()
