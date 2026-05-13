"""日志系统 — loguru 封装"""

import sys

from loguru import logger

from src.core.config import get_config


def setup_logging() -> None:
    """初始化日志系统"""
    config = get_config()
    log_config = config.logging

    logger.remove()

    logger.add(
        sys.stderr,
        level=log_config.level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
    )

    logger.add(
        log_config.file,
        level=log_config.level,
        rotation=log_config.rotation,
        retention=log_config.retention,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    )

    logger.info("日志系统已初始化")
