# 🚨 Balistika Alarm Bot

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.x-green)
![kurigram](https://img.shields.io/badge/kurigram-pyrogram%20fork-blue)
![gemini](https://img.shields.io/badge/google--genai-latest-orange)
![License](https://img.shields.io/badge/license-MIT-yellow)

**Balistika Alarm Bot** is a Telegram bot that monitors the official Ukrainian air alert API and supplements it with real-time AI analysis of Telegram channels to instantly notify subscribed users about direct missile threats to their city.

---

## ✨ Features

- 🚀 **Missile Threat Filtering:** Polls the [alerts.in.ua](https://alerts.in.ua/) API every 10 seconds and activates exclusively for red-level missile threats (`ballistic_missiles`, `cruise_missiles`, `unspecified_missiles`).
- 🤖 **AI-Powered Channel Monitoring:** When an official missile threat is declared, the bot activates a built-in userbot (Kurigram, a maintained Pyrogram fork) that monitors specific Telegram channels. It feeds the messages to Google's Gemini AI to determine if a threat is active (`THREAT`), passed (`CLEAR`), or irrelevant (`IGNORE`).
- 🔕 **Smart Mute:** After the first warning, users are automatically muted to prevent spam. They receive the all-clear message when the threat ends, or can unmute manually at any time to receive subsequent warnings.
- ⚙️ **Granular Settings:** Users can individually opt in or out of official "Clear" messages and AI-generated "Probably clear" messages.
- 📊 **Status Dashboard:** Users can check the current alert state, active threat types, activation status, mute status, and AI channel status via a button.
- 💾 **Persistent Storage:** User preferences are stored in a local SQLite database via `aiosqlite`. Missing columns are added automatically on startup, so existing databases keep working after updates.
- 🔑 **Code-free Userbot Login:** The userbot authenticates with a session string created once via QR login, so the server never needs an interactive login or a confirmation code.

---

## 🏗 Architecture

```text
main.py        — Bot entry point, handlers, alert broadcast loop
alarm.py       — API client for alerts.in.ua
userbot.py     — Kurigram/Pyrogram channel monitor with polling logic
ai.py          — Gemini-based ThreatAnalyzer
database.py    — SQLite operations (users, mute, active, clear preferences)
qr_login.py    — One-time QR login that produces the PYRO_SESSION string
config.cfg     — City and monitored channels configuration
.env           — Tokens, API keys and session string (not committed)
```

**How the dual-level alert loop works:**

1. **Idle Mode:** The bot queries the alerts API every 10 seconds. The userbot sleeps and makes no requests to the Telegram API.
2. **Official Alert:** If a new threat is detected (`alert_level == "red"` AND a missile threat is present):
   - Broadcasts `🔴 Danger!` to all active, unmuted users and mutes everyone.
   - Wakes up the userbot (`set_listening(True)`), which immediately fetches the last 10 messages from monitored channels for context.
3. **AI Monitoring:** The userbot polls monitored channels every 10 seconds and analyzes new messages with Gemini.
   - On `CLEAR`, it sends `🟢 Probably clear.` to users who enabled AI clear messages (they stay muted until the official all-clear).
   - On `THREAT`, it sends `🔴 Danger!` to anyone who manually unmuted.
4. **End of Alert:** When the official API downgrades or clears the alert:
   - The userbot goes back to sleep.
   - Broadcasts `🟢 Clear.` to muted users who opted in, and unmutes everyone.
