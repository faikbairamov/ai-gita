# Telegram Reminder Agent

This repository contains a simple example of using LangChain with Google's
Gemini model to parse natural language reminder requests and send them via a
Telegram bot.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables:
   - `TELEGRAM_BOT_TOKEN` – token for your Telegram bot.
   - `GOOGLE_API_KEY` – API key for Gemini.

## Run

```bash
python telegram_reminder_agent.py
```

Send the bot a message such as "Remind me to take drugs tomorrow at 2pm" and it
will schedule a reminder and send a message at the specified time.
