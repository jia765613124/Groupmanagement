from contextlib import asynccontextmanager
import logging
from typing import Annotated
from aiogram.types import Update
from fastapi import FastAPI, Header
from starlette.middleware.cors import CORSMiddleware

from bot.config import get_config
from bot.misc import dp, bot
from bot.utils import setup_logging

config = get_config()
setup_logging(config)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("🚀 Starting application")
    from bot.main import setup_webhook

    await setup_webhook(bot)
    yield
    await bot.delete_webhook()
    logger.info("⛔ Stopping application, deleting webhook")


app = FastAPI(title=config.API_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(config.WEBHOOK_PATH)
async def webhook(
    update: dict,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> None | dict:
    if x_telegram_bot_api_secret_token != config.BOT_SECRET_TOKEN:
        logger.error("Wrong secret token!")
        return {"status": "error", "message": "Wrong secret token !"}
    telegram_update = Update(**update)
    # logger.debug("Webhook update: %s", telegram_update)
    await dp.feed_webhook_update(bot=bot, update=telegram_update)
    return {"ok": True}
