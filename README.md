# Safe Mode for Claude Code

**Use Claude Code without worrying about what it can do to your computer.** Safe Mode checks every command and file Claude touches, blocks the dangerous ones, and asks you in plain English before anything risky:

```
⚠ Claude wants to permanently delete a folder and everything inside it (it won't go to the Recycle Bin).
Command: Remove-Item .\Documents\old -Recurse -Force
Safe Mode: only allow this if you expected it.
```

Built for people who aren't developers: no jargon, one-step install, works on **Windows (PowerShell)**, macOS and Linux.

## What it does

**Always blocked**, no matter what mode you're in:
- Your SSH keys, cloud credentials (AWS, Docker, GPG)
- Your browser's saved passwords and cookies (Chrome, Edge, Brave, Firefox)
- Windows' saved passwords, password manager vaults, crypto wallets
- Erasing a drive or deleting your whole home folder

**Asks you first**, with a plain-English warning:
- Deleting a folder or everything matching `*`
- Throwing away unsaved work (`git reset --hard`, `git clean`) or overwriting GitHub history (`git push --force`)
- Downloading a script and running it immediately (`curl ... | bash`, `irm ... | iex`)
- Uploading files from your computer to a website
- Changing system or security settings, installing programs globally, shutting down
- Reading `.env`, `secrets.json` and other files that usually hold passwords or API keys

Everything else works exactly as before. Safe Mode's questions still appear in **auto mode**, which normally skips most prompts.

**`/safety-check`** gives you a report: is Safe Mode on, are any of your settings risky, and what was blocked this week.

## Install (2 minutes)

You need Python 3.8+ (`python --version`).

1. Download this repo (green **Code** button → **Download ZIP**) and unzip it somewhere permanent, e.g. `Documents/safe-mode`.
2. In that folder, run:
   ```
   python install.py
   ```
   (`python3 install.py` on macOS/Linux.)
3. Restart Claude Code and type `/safety-check`.

The installer backs up your `~/.claude/settings.json` first and keeps all your existing settings. To uninstall: `python install.py --remove`.

## Good to know

- Safe Mode is a **seatbelt, not a vault**. It catches the common ways things go wrong, but a determined program could find a way around pattern checks. Keep backups of anything important.
- Nothing leaves your computer. Decisions are logged locally to `~/.claude/safe-mode/log.jsonl` for `/safety-check`.
- If Safe Mode itself ever crashes, Claude Code carries on with its normal permission prompts.

## Also by me

**[Budget Coach](https://github.com/reillyb732-lab/claude-code-budget-coach)**: a free status line that warns you *before* you hit your Claude usage limit.

## License

MIT
