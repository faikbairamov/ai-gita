"""Telegram reminder bot using LangChain with Gemini API.

This bot listens to messages on Telegram and uses a Gemini-powered
LangChain chain to parse reminder requests. When a user sends a message like
"Remind me to take drugs tomorrow at 2pm", the bot schedules a reminder and
sends the user a Telegram message at the requested time.

Environment variables required:
- TELEGRAM_BOT_TOKEN: token for your Telegram bot.
- GOOGLE_API_KEY: API key for the Google Gemini service.

Run with:
    python telegram_reminder_agent.py
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

# Define how the LLM should format its response
RESPONSE_SCHEMAS = [
    ResponseSchema(name="task", description="task to remind the user about"),
    ResponseSchema(
        name="time",
        description="ISO 8601 timestamp for when the reminder should occur (in UTC)",
    ),
]
OUTPUT_PARSER = StructuredOutputParser.from_response_schemas(RESPONSE_SCHEMAS)
FORMAT_INSTRUCTIONS = OUTPUT_PARSER.get_format_instructions()

PROMPT = PromptTemplate(
    template=(
        "Extract a reminder from the message.\n"
        "{format_instructions}\n"
        "Message: {message}"
    ),
    input_variables=["message"],
    partial_variables={"format_instructions": FORMAT_INSTRUCTIONS},
)

LLM = ChatGoogleGenerativeAI(
    model="gemini-pro", google_api_key=os.environ.get("GOOGLE_API_KEY", "")
)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and schedule reminders."""
    user_text = update.message.text

    chain = PROMPT | LLM | OUTPUT_PARSER
    parsed = chain.invoke({"message": user_text})
    task = parsed["task"]
    time_str = parsed["time"]
    remind_time = datetime.fromisoformat(time_str)
    if remind_time.tzinfo is None:
        remind_time = remind_time.replace(tzinfo=timezone.utc)

    chat_id = update.effective_chat.id
    delay = remind_time - datetime.now(timezone.utc)
    context.job_queue.run_once(send_reminder, when=delay, chat_id=chat_id, data=task)

    await update.message.reply_text(
        f"Got it! I'll remind you to {task} at {remind_time.isoformat()}"
    )


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the reminder message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Reminder: {job.data}")


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable not set")

    application = ApplicationBuilder().token(token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()


if __name__ == "__main__":
    main()
