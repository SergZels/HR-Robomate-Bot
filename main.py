from aiogram import  Dispatcher
from aiogram.types import Update
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
import uvicorn
import asyncio
import os
from contextlib import asynccontextmanager
from biznesLogic import router, logger
from init import bot,SERV,WebhookURL,URL
from fastapi.middleware.cors import CORSMiddleware

dp = Dispatcher()
dp.include_routers(router)


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
origins = [
   "http://localhost",
   "http://127.0.0.1",
   "http://localhost:5033",
 ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(f'/{URL}/webhook')
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)

@app.get(f'/{URL}', response_class=HTMLResponse)
async def resumes(request: Request):
    return "Resume list"


@app.get(f"/{URL}/logs", response_class=HTMLResponse)
async def get_logs(request: Request):
    log_file_path = "Logfile.txt"  # Вкажіть шлях до вашого файлу логів
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r", encoding="utf-8") as file:
                content = file.readlines()
                last_100_lines = ''.join(content[-100:])
            html_content = f"""
                <html>
                    <body>
                        <h1>Логи</h1>
                        <pre>{last_100_lines}</pre>
                    </body>
                </html>
                """
            return HTMLResponse(content=html_content)
        except:
            print("файл не відкрився")
    else:
        return "<html><body><h1>Файл логів не знайдено</h1></body></html>"

if __name__ == "__main__":
    port = 3021 if SERV else 3055
    uvicorn.run(app, host="127.0.0.1", port=port)