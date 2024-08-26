import asyncio

from telegram import Bot
from telegram.error import TelegramError


class TelegramSender:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    #  async def send_telegram_message(token, chat_id, message):
    async def _send_telegram_message(self, message, mode=None):
        bot = Bot(token=self.token)
        try:
            await bot.send_message(chat_id=self.chat_id, text=message, parse_mode=mode)
        except TelegramError as e:
            print(f"An error occurred: {e}")

    def send_telegram_message(self, message):
        asyncio.run(self._send_telegram_message(message))

    def send_telegram_markdown(self, message):
        asyncio.run(self._send_telegram_message(message, mode="MarkdownV2"))

    def send_telegram_html(self, message):
        asyncio.run(self._send_telegram_message(message, mode="HTML"))
