import asyncio
import logging

import uvicorn

from bot.config import get_config
from bot.main import start_pooling
from bot.utils import setup_logging
from api import app

config = get_config()
setup_logging(config)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if config.USE_WEBHOOK:
        logger.info("Starting webhook DEBUG server USE_WEBHOOK: %s", config.DEBUG)
        if config.DEBUG:
            uvicorn.run(
                "api:app",
                host="0.0.0.0",
                port=6100,
                reload=True,
                reload_dirs=["bot"],
                log_level="debug"
            )
        else:
          uvicorn.run(app, host="0.0.0.0", port=6100)
          logger.info("Starting webhook DEBUG server USE_WEBHOOK: %s", config.DEBUG)
    else:
        logger.info("Starting bot polling")
        asyncio.run(start_pooling())
