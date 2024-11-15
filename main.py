from aiogram import  Dispatcher
from aiogram.types import Update
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from biznesLogic import router, logger
import json
from init import bot,SERV,WebhookURL,URL,redis
from fastapi.templating import Jinja2Templates

dp = Dispatcher()
dp.include_routers(router)
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if SERV:
        await bot.set_webhook(url=WebhookURL,
                                  allowed_updates=dp.resolve_used_update_types(),
                                  drop_pending_updates=True)
        yield
        await bot.delete_webhook()
    else:
        await bot.delete_webhook()
        polling_task = asyncio.create_task(dp.start_polling(bot))
        yield
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

@app.post(f'/{URL}/webhook')
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)

@app.get(f'/{URL}', response_class=HTMLResponse)
async def resumes(request: Request,cache_key:str):
    cached_data = await redis.get(cache_key)
    if cached_data:
        resumes = json.loads(cached_data)
        return templates.TemplateResponse('index.html', {
            "request": request,
            "resumes": resumes,
        })

    return "Resumes not found"


if __name__ == "__main__":
    port = 3021 if SERV else 5000
    uvicorn.run(app, host="0.0.0.0", port=port)