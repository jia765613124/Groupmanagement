import logging
import sys
from pathlib import Path
from typing import Any

def setup_logging(config: Any = None):
    """设置日志配置"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "bot.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Set specific level for wallet module to capture detailed logs
    logging.getLogger("bot.utils.wallet").setLevel(logging.DEBUG) 