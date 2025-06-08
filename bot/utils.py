import logging
import sys
from bot.config import Config


def setup_logging(config: Config) -> None:
    logging_level = logging.DEBUG if config.DEBUG else logging.INFO
    logging.basicConfig(level=logging_level, stream=sys.stdout)
