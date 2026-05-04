"""TelegramNotifier — отправляет сообщения через aiogram Bot."""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str | None = None) -> None:
        self._bot = Bot(token=bot_token)
        self._default_chat_id = chat_id
        self._chat_ids: list[int] = []
        if chat_id:
            try:
                self._chat_ids = [int(chat_id)]
            except (ValueError, TypeError):
                logger.warning("Invalid chat_id: %s", chat_id)

    def set_recipients(self, chat_ids: list[int]) -> None:
        """Установить список получателей."""
        self._chat_ids = chat_ids

    async def send(self, text: str) -> None:
        """Отправить сообщение всем получателям (или default chat_id)."""
        recipients = self._chat_ids if self._chat_ids else (
            [int(self._default_chat_id)] if self._default_chat_id else []
        )

        if not recipients:
            logger.warning("No recipients configured")
            return

        for chat_id in recipients:
            try:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logger.error("Telegram send to %s failed: %s", chat_id, e)

    async def close(self) -> None:
        await self._bot.session.close()
