from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import os
from aiogram.enums import ParseMode

load_dotenv()
SERV = os.getenv("server") == 'production'

if SERV:
    API_TOKEN = os.getenv("API_TOKEN")
    TELEGRAM_API_URL = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
else:
    API_TOKEN = os.getenv("API_TOKEN_Test")
    TELEGRAM_API_URL = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'

URL = os.getenv("URL")
WebhookURL= os.getenv("WebhookURL")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
