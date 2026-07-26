```python
"""
ByToBy Pro 2.0
Professional Logging System
"""

from __future__ import annotations

import logging
import sys
import time
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ==========================================================
# Console Colors
# ==========================================================

class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


# ==========================================================
# Console Formatter
# ==========================================================

class ConsoleFormatter(logging.Formatter):

    COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.MAGENTA,
    }

    def format(self, record):

        color = self.COLORS.get(record.levelno, Colors.GREEN)

        level = f"{color}{record.levelname:<8}{Colors.RESET}"

        return (
            f"{record.asctime} | "
            f"{level} | "
            f"{record.name:<15} | "
            f"{record.getMessage()}"
        )


# ==========================================================
# Logger Class
# ==========================================================

class Logger:

    _instances = {}

    def __new__(cls, name="ByToBy"):

        if name not in cls._instances:

            cls._instances[name] = super().__new__(cls)
            cls._instances[name]._initialize(name)

        return cls._instances[name]

    def _initialize(self, name):

        self.logger = logging.getLogger(name)

        self.logger.setLevel(logging.DEBUG)

        self.logger.propagate = False

        if self.logger.handlers:
            return

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        console_formatter = ConsoleFormatter(
            "%(asctime)s"
        )

        # ==================================================
        # Main Log
        # ==================================================

        file_handler = RotatingFileHandler(
            log_dir / f"{name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )

        file_handler.setFormatter(file_formatter)

        # ==================================================
        # Error Log
        # ==================================================

        error_handler = RotatingFileHandler(
            log_dir / f"{name}_error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )

        error_handler.setLevel(logging.ERROR)

        error_handler.setFormatter(file_formatter)

        # ==================================================
        # Console
        # ==================================================

        console = logging.StreamHandler(sys.stdout)

        console.setFormatter(console_formatter)

        # ==================================================

        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console)

    def get(self):

        return self.logger


# ==========================================================
# Default Logger
# ==========================================================

logger = Logger().get()


# ==========================================================
# Streamlit Helpers
# ==========================================================

def st_info(message: str):

    logger.info(message)

    try:
        import streamlit as st
        st.info(message)
    except Exception:
        pass


def st_warning(message: str):

    logger.warning(message)

    try:
        import streamlit as st
        st.warning(message)
    except Exception:
        pass


def st_error(message: str):

    logger.error(message)

    try:
        import streamlit as st
        st.error(message)
    except Exception:
        pass


def st_success(message: str):

    logger.info(message)

    try:
        import streamlit as st
        st.success(message)
    except Exception:
        pass


# ==========================================================
# Execution Time Decorator
# ==========================================================

def timer(func):

    @wraps(func)

    def wrapper(*args, **kwargs):

        start = time.perf_counter()

        try:

            result = func(*args, **kwargs)

            elapsed = time.perf_counter() - start

            logger.info(
                f"{func.__name__} finished in {elapsed:.3f}s"
            )

            return result

        except Exception:

            logger.exception(
                f"Exception inside {func.__name__}"
            )

            raise

    return wrapper


# ==========================================================
# Call Decorator
# ==========================================================

def log_call(func):

    @wraps(func)

    def wrapper(*args, **kwargs):

        logger.debug(
            f"Calling {func.__name__}"
        )

        return func(*args, **kwargs)

    return wrapper


# ==========================================================
# Helper
# ==========================================================

def get_logger(name="ByToBy"):

    return Logger(name).get()
```
