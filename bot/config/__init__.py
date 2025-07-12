# bot.config package

# 重新定义配置以避免循环导入
from functools import lru_cache
from typing import final

from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

# 环境变量文件名
ENV_FILE_NAME = ".env"

from bot.config.multi_game_config import MultiGameConfig
from bot.config.lottery_config import LotteryConfig

# 全局配置实例
multi_game_config = MultiGameConfig()
lottery_config = LotteryConfig()

@final
class Config(BaseSettings):
    """
    配置类
    用于管理应用程序的所有配置项
    """
    model_config = SettingsConfigDict(env_file=ENV_FILE_NAME)

    # Bot配置
    BOT_TOKEN: str  # 机器人令牌
    ADMIN_IDS: list[int] = [
        123123,
    ]  # 管理员ID列表
    DEBUG: bool = False  # 调试模式
    USE_WEBHOOK: bool = False  # 是否使用Webhook
    BOT_SECRET_TOKEN: str | None = None  # Webhook密钥

    # Telethon配置
    API_ID: int  # Telegram API ID
    API_HASH: str  # Telegram API Hash
    PHONE_NUMBER: str  # 手机号码

    # API配置
    API_NAME: str = "Telegram Bot API"  # API名称
    API_V1_STR: str = "/api/v1"  # API版本路径
    API_HOST: str  # API主机地址
    API_PORT: int | None = None  # API端口
    ORIGINS: list[str] = [
        "http://bot.arturboyun.com",
        "https://bot.arturboyun.com",
        "http://localhost",
        "http://localhost:8000",
    ]  # 允许的源地址列表

    # 数据库配置
    DB_HOST: str = "localhost"  # 数据库主机
    DB_PORT: int = 3306  # 数据库端口
    DB_USER: str = "root"  # 数据库用户名
    DB_PASSWORD: str  # 数据库密码
    DB_NAME: str = "tg_search_bot"  # 数据库名称
    REDIS_DSN: RedisDsn  # Redis数据库连接字符串

    # 钱包配置
    WALLET_ADDRESS: str  # 钱包地址

    # 钓鱼通知群组配置
    fishing_notification_groups: str = ""  # 通知群组ID，逗号分隔
    checkin_allowed_groups: str = ""  # 允许签到的群组ID，逗号分隔
    subscription_link: str = "https://t.me/your_channel"  # 钓鱼通知中的订阅链接

    @property
    def MYSQL_DSN(self) -> str:
        """
        构建 MySQL DSN
        """
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def WEBHOOK_PATH(self) -> str:
        """
        获取Webhook路径
        """
        return f"/webhook2"

    @property
    def WEBHOOK_URL(self) -> str:
        """
        获取完整的Webhook URL
        """
        return f"{self.API_HOST}{self.WEBHOOK_PATH}"


@lru_cache
def get_config() -> Config:
    """
    获取配置实例
    使用缓存装饰器确保只创建一个配置实例
    """
    return Config()  # type: ignore


def get_multi_game_config() -> MultiGameConfig:
    """获取多群组配置实例"""
    return multi_game_config

def get_lottery_config() -> LotteryConfig:
    """获取单群组配置实例（向后兼容）"""
    return lottery_config

__all__ = ['get_config', 'Config'] 