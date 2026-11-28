from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING
import colorama

if TYPE_CHECKING:
    from typing import Optional
    from pathlib import Path

__all__ = ['config_app_logger']


class LogLevelColorizer(logging.Filter):
    level2ansi = {
        logging.DEBUG: colorama.Fore.CYAN + colorama.Style.BRIGHT,
        logging.INFO: colorama.Fore.GREEN + colorama.Style.BRIGHT,
        logging.WARNING: colorama.Fore.YELLOW + colorama.Style.BRIGHT,
        logging.ERROR: colorama.Fore.RED + colorama.Style.BRIGHT,
        logging.CRITICAL: colorama.Back.RED + colorama.Fore.WHITE + colorama.Style.BRIGHT
    }

    def filter(self, record: logging.LogRecord) -> bool:
        record.header_color = self.level2ansi.get(record.levelno, "")
        return True


def config_app_logger(
    name: str=None,
    level: int=logging.INFO,
    log_directory: Optional[Path]=None,
    terminal_logging: bool=True
) -> None:
    app_logger = logging.getLogger(name)
    for handler in app_logger.handlers.copy():
        app_logger.removeHandler(handler)
        handler.close()

    app_logger.setLevel(level)
    app_logger.propagate = False

    header_fmt = "%(asctime)s | %(levelname)-8s | %(processName)s | %(name)s"
    formatter_kwargs = dict(
        datefmt = "%Y-%m-%d %H:%M:%S",
        style='%',
    )

    # prints log messages in the terminal
    if terminal_logging:
        log_term_formatter = logging.Formatter(
            f"%(header_color)s{header_fmt} |{colorama.Style.RESET_ALL} %(message)s",
            **formatter_kwargs
        )
        term_handler = logging.StreamHandler()
        term_handler.setLevel(level)
        term_handler.setFormatter(log_term_formatter)
        term_handler.addFilter(LogLevelColorizer())
        app_logger.addHandler(term_handler)

    # writes log message in a log file
    if log_directory is not None:
        log_directory.mkdir(parents=True, exist_ok=True)
        log_file_formatter = logging.Formatter(
            f"{header_fmt} | %(message)s",
            **formatter_kwargs
        )
        file_handler = RotatingFileHandler(
            log_directory.joinpath("logfile.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(log_file_formatter)
        app_logger.addHandler(file_handler)
