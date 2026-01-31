import inspect
import logging
import sys
from os import getenv

from loguru import logger

logger.level("WARN", no=30, color="<yellow>")
logger.level("PASS", no=20, color="<green>")

logger.warning = lambda msg, *args, **kwargs: logger.opt(depth=1).log("WARN", msg, *args, **kwargs)
logger.success = lambda msg, *args, **kwargs: logger.opt(depth=1).log("PASS", msg, *args, **kwargs)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            if record.levelno == logging.WARNING:
                level: str | int = "WARN"
            else:
                level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logger.remove(0)

if getenv("LOG_HI", True):
    logger.add(
        sink=sys.stderr,
        colorize=True,
        enqueue=True,
        format=(
            "<light-green>{time:YYYY-MM-DD--HH:mm:ss}</light-green> "
            "| <level>{level: <5}</level> | "
            "<light-cyan>{name}:{function}:{line} </light-cyan> - "
            "{message}"
        ),
    )
logging.basicConfig(handlers=[InterceptHandler()], level=getenv("LOG_LEVEL", 0), force=True)
