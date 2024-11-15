from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import os
from aiogram.enums import ParseMode
import redis.asyncio as aioredis
from dataclasses import dataclass, field

load_dotenv()
SERV = os.getenv("server") == 'production'

if SERV:
    API_TOKEN = os.getenv("API_TOKEN")
    TELEGRAM_API_URL = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
else:
    API_TOKEN = os.getenv("API_TOKEN_Test")
    TELEGRAM_API_URL = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'

URL = ''  #os.getenv("URL")
WebhookURL= os.getenv("WebhookURL")
redis = aioredis.from_url("redis://localhost:6379", decode_responses=True)
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))



@dataclass
class LanguageLevel:
    levels: dict[str, int] = field(default_factory=lambda: {
        "середній": 1,
        "вище середнього": 3,
        "просунутий": 6,
        "вільно": 10,
    })

@dataclass
class DateResumePoints:
    points: dict[str, int] = field(default_factory=lambda: {
        "d<=1": 3,
        "1<d<=7": 2,
        "7<d<14": 1,
    })

@dataclass
class PointsConfig:
    language: LanguageLevel = field(default_factory=LanguageLevel)
    skill: int = 0.5
    skill_match: int = 5
    experience_month: float = 0.2
    date_resume: DateResumePoints = field(default_factory=DateResumePoints)