from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
import re
import logging
import os
from init import bot, TELEGRAM_API_URL
import aiohttp
import asyncio

router = Router()


class AsyncFileHandler(logging.FileHandler):  # для асинхронного логування
    def emit(self, record):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, super().emit, record)


logger = logging.getLogger('async_logger')
logger.setLevel(logging.INFO)
handler = AsyncFileHandler('Logfile.txt')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


async def send_telegram_message(chat_id, text):
    payload = {
        'chat_id': chat_id,
        'text': text
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(TELEGRAM_API_URL, json=payload) as response:
                response.raise_for_status()  # Якщо статус відповіді не 200, підніме виключення
                logger.info(f"Надіслано повідомлення користувачу {chat_id}")
                return await response.json()

        except aiohttp.ClientError as e:
            logger.info(f"Помилка при надсиланні телеграм повідомлення до {chat_id}: {e}")
            print(f"Помилка при надсиланні телеграм повідомлення до {chat_id}: {e}")
            return None


@router.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject) -> None:
    await message.answer("Start")


@router.message(F.text.lower() == "/help")
async def answer_yes(message: Message):
    await message.answer("Для отримання допомоги напишіть будь-ласка на @SZelinsky", )




