"""Safe Mode for Claude Code: a PreToolUse hook that stops risky actions and explains them in plain English.

Claude Code runs this before every shell command and file access. It answers:
  - "deny": never allowed (your passwords, keys, browser data, wiping disks)
  - "ask":  you must confirm, with a plain-English warning (mass deletes, uploads, force-push...)
  - nothing: normal Claude Code permissions apply

"ask" still forces a prompt in auto mode. Every deny/ask is logged so /safety-check can report it.
"""
import json
import re
import sys
import time
from pathlib import Path

LOG = Path.home() / ".claude" / "safe-mode" / "log.jsonl"

# (pattern, decision, plain-English reason). Matched case-insensitively against paths and commands.
PROTECTED = [
    (r"[\\/]\.ssh([\\/]|$)|id_(rsa|ed25519|ecdsa)", "deny", "your SSH keys (they unlock servers and GitHub)"),
    (r"[\\/]\.aws[\\/]|[\\/]\.gnupg([\\/]|$)|[\\/]\.docker[\\/]config\.json", "deny", "your cloud and signing credentials"),
    (r"(chrome|edge|brave|chromium)[\\/]user data|firefox[\\/]profiles|login data|[\\/]cookies(\.sqlite)?$",
     "deny", "your browser's saved passwords and logins"),
    (r"microsoft[\\/](credentials|protect|vault)", "deny", "Windows' saved passwords"),
    (r"\.(kdbx|1pux|opvault)$|[\\/]wallet\.dat$|[\\/](exodus|electrum|metamask)", "deny", "a password manager or crypto wallet"),
    (r"\.(pem|p12|pfx)$", "ask", "a security certificate or private key"),
    (r"(^|[\\/\s\"'])\.env(\.(?!example|sample|template)\w+)?(\s|[\"']|$)|secrets?\.json|credentials\.json",
     "ask", "a file that usually holds passwords or API keys"),
]

COMMANDS = [
    # wiping disks and system damage: never
    (r"\bformat(\.com)?\s+[a-z]:|\bdiskpart\b|\bmkfs\b|\bdd\s+.*\bof=/dev/", "deny", "erase a whole drive"),
    (r"\b(rm|remove-item|ri|rd|rmdir)\s+(-\w+\s+|/\w\s+)*[\"']?(/|~|\$home|\$env:userprofile|c:[\\/]?)[\"']?(\s+[-/]\w+)*\s*$",
     "deny", "delete your entire drive or home folder"),
    # deleting lots of files
    (r"\brm\s+(-\w*[rR]\w*|--recursive)\b", "ask",
     "permanently delete a folder and everything inside it (it won't go to the Recycle Bin)"),
    (r"remove-item\b.*-r(ecurse)?\b|\b(rmdir|rd)\s+/s\b|\bdel\s+.*/s\b", "ask",
     "permanently delete a folder and everything inside it (it won't go to the Recycle Bin)"),
    (r"\b(rm|del|remove-item|ri)\s+[^|;&]*\*", "ask", "delete every file matching a wildcard (*)"),
    # git: losing work
    (r"\bgit\s+push\b.*(--force\b|-f\b|--force-with-lease)", "ask",
     "overwrite the history on GitHub, which can erase your (or others') saved work"),
    (r"\bgit\s+(reset\s+--hard|clean\s+-\w*f|checkout\s+(--\s+)?\.\s*$|restore\s+\.)", "ask",
     "throw away all your unsaved changes for good"),
    # running code from the internet
    (r"(curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)\b[^|]*\|\s*(sudo\s+)?(bash|sh|zsh|iex|invoke-expression|python3?|pwsh|powershell)\b",
     "ask", "download a script from the internet and run it immediately, without you seeing it first"),
    # sending your files somewhere
    (r"\bcurl(\.exe)?\b.*(\s-T\s|--upload-file|\s-F\s|--form|(-d|--data(-binary|-raw)?)\s+@)", "ask",
     "upload a file from your computer to a website"),
    (r"invoke-(webrequest|restmethod)\b.*(-infile|-method\s+(post|put))", "ask",
     "send data from your computer to a website"),
    (r"\b(scp|rsync|sftp)\b.*:", "ask", "copy files from your computer to another machine"),
    # system and security settings
    (r"set-executionpolicy|\breg(\.exe)?\s+(add|delete|import)|bcdedit|netsh\s+advfirewall|set-mppreference|"
     r"disable-windowsoptionalfeature|\bsudo\b|\bchmod\s+-R\s+777", "ask",
     "change your computer's system or security settings"),
    (r"\b(shutdown|stop-computer|restart-computer)\b", "ask", "shut down or restart your computer"),
    (r"\b(npm|pip|pip3|winget|choco|brew)\s+(install|i)\b.*\s-g\b|\bnpm\s+(install|i)\s+-g\b", "ask",
     "install a program for your whole computer"),
]

FILE_TOOLS = {"Read": "read", "Edit": "edit", "Write": "write", "NotebookEdit": "edit", "Glob": "search", "Grep": "search"}
SHELL_TOOLS = {"Bash", "PowerShell"}


def check(tool, tool_input):
    """Return (decision, message) or None."""
    if tool in SHELL_TOOLS:
        cmd = tool_input.get("command", "")
        hits = [(d, f"Claude wants to {why}.") for pat, d, why in COMMANDS if re.search(pat, cmd, re.I)]
        hits += [(d, f"This command touches {why}.") for pat, d, why in PROTECTED if re.search(pat, cmd, re.I)]
        if hits:
            hits.sort(key=lambda h: h[0] != "deny")  # deny wins
            return hits[0][0], f"{hits[0][1]}\nCommand: {cmd[:300]}"
    elif tool in FILE_TOOLS:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path") or ""
        for pat, d, why in PROTECTED:
            if path and re.search(pat, path, re.I):
                return d, f"Claude wants to {FILE_TOOLS[tool]} {why}.\nFile: {path}"
    return None


def log(event, decision, message):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"t": int(time.time()), "tool": event.get("tool_name"), "decision": decision,
                                "mode": event.get("permission_mode"), "why": message.splitlines()[0]}) + "\n")
    except OSError:
        pass


def main():
    try:
        event = json.load(sys.stdin)
        result = check(event.get("tool_name", ""), event.get("tool_input") or {})
    except Exception:
        return  # never break Claude Code; no output = normal permissions apply
    if not result:
        return
    decision, message = result
    log(event, decision, message)
    footer = ("Safe Mode blocked this. If you really need it, do it yourself outside Claude."
              if decision == "deny" else "Safe Mode: only allow this if you expected it.")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"⚠ {message}\n{footer}",
    }}))


if __name__ == "__main__":
    main()
