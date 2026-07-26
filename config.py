"""
ByToBy Pro 2.0
Central Configuration
"""

from __future__ import annotations

import os
import streamlit as st
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _get_secret(name: str, default: str = "") -> str:
    """
    يحاول القراءة من:
    1- Streamlit Secrets
    2- Environment Variables
    """

    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return os.getenv(name, default)


@dataclass(frozen=True)
class AppConfig:

    APP_NAME: str = "ByToBy Pro"

    VERSION: str = "2.0"

    DEBUG: bool = True

    DEFAULT_EXCHANGE: str = "NASDAQ"

    DEFAULT_PERIOD: str = "1y"

    DEFAULT_INTERVAL: str = "1d"

    MAX_SYMBOLS: int = 100

    CACHE_MINUTES: int = 5

    AUTO_REFRESH_SECONDS: int = 300


@dataclass(frozen=True)
class APIKeys:

    FINNHUB: str = _get_secret("FINNHUB_API_KEY")

    POLYGON: str = _get_secret("POLYGON_API_KEY")

    FMP: str = _get_secret("FMP_API_KEY")

    TIINGO: str = _get_secret("TIINGO_API_KEY")

    NEWSAPI: str = _get_secret("NEWS_API_KEY")

    TELEGRAM_TOKEN: str = _get_secret("TELEGRAM_BOT_TOKEN")

    TELEGRAM_CHAT_ID: str = _get_secret("TELEGRAM_CHAT_ID")


@dataclass(frozen=True)
class ScannerConfig:

    MIN_PRICE = 1

    MAX_PRICE = 500

    MIN_VOLUME = 300000

    MIN_DOLLAR_VOLUME = 5_000_000

    RSI_LOW = 45

    RSI_HIGH = 70

    ADX_MIN = 25

    MIN_RELATIVE_VOLUME = 1.5

    MIN_AI_SCORE = 70


config = AppConfig()

api = APIKeys()

scanner = ScannerConfig()
