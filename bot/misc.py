# Dispatcher
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage

from bot.config import get_config

# 获取配置
config = get_config()

# 设置Redis存储的键构建器
key_builder = DefaultKeyBuilder(with_destiny=True)
# 初始化Redis存储，设置状态和数据过期时间为2小时（7200秒）
storage = RedisStorage.from_url(
    str(config.REDIS_DSN),
    key_builder=key_builder,
    state_ttl=7200,  # 状态数据2小时后过期
    data_ttl=7200    # 普通数据2小时后过期
)
# 创建调度器
dp = Dispatcher(storage=storage)

# Bot
# 设置默认机器人属性，使用HTML解析模式
default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
# 创建机器人实例
bot = Bot(token=config.BOT_TOKEN, default=default_bot_properties)
