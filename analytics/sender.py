"""Send reports via Telegram Bot API."""

import asyncio
from telegram import Bot
from telegram.constants import ParseMode

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


async def _send(text, chat_id=None):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    target = chat_id or TELEGRAM_CHAT_ID
    await bot.send_message(
        chat_id=target,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )


def send_report(text, chat_id=None):
    asyncio.run(_send(text, chat_id))
