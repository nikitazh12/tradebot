"""TelegramNotifier — отправляет сообщения через aiogram Bot."""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot = Bot(token=bot_token)
        self._chat_id = chat_id

    async def send(self, text: str) -> None:
        try:
            await self._bot.send_message(
                chat_id=self._chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.error("Telegram send failed: %s", e)

    async def close(self) -> None:
        await self._bot.session.close()
