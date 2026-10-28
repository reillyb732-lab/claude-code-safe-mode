---
name: safety-check
description: Show a plain-English report of how well Claude Code is protecting this computer (Safe Mode status, risky settings, what was blocked this week). Use when the user types /safety-check or asks whether Claude Code is safe or what it has access to.
---

Run the Safe Mode report and explain it to the user in plain, non-technical language:

1. Find `safety_check.py`: it sits next to the `safe_mode.py` path in the Safe Mode hook command in `~/.claude/settings.json`. Run it with the same Python that command uses.
2. Show the report, then in 2–4 sentences say what is protected, what (if anything) to fix, and how to fix it. Don't change any settings unless the user asks.
