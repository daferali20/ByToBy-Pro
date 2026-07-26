```python
"""
ByToBy Pro
Yahoo Finance API Layer
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests
import yfinance as yf

from utils.cache import cache, cached
from utils.logger import get_logger, timer


logger = get_logger("YahooAPI")


class YahooAPI:
    """
    Professional Yahoo Finance API Wrapper
    """

    def __init__(
        self,
        timeout: int = 15,
        retries: int = 3,
    ):

        self.timeout = timeout
        self.retries = retries

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept":
                    "application/json,text/plain,*/*",
            }
        )

        logger.info("Yahoo API Initialized")

    # =====================================================
    # Internal Helpers
    # =====================================================

    def _request(self, symbol: str) -> yf.Ticker | None:
        """
        Return Yahoo Ticker object.
        """

        try:

            ticker = yf.Ticker(symbol)

            return ticker

        except Exception as e:

            logger.exception(e)

            return None

    def _retry(self, func, *args, **kwargs):

        last_error = None

        for attempt in range(self.retries):

            try:

                return func(*args, **kwargs)

            except Exception as e:

                last_error = e

                logger.warning(
                    f"Retry {attempt+1}/{self.retries}"
                )

                time.sleep(1)

        logger.exception(last_error)

        return None

    # =====================================================
    # Validation
    # =====================================================

    def validate_symbol(self, symbol: str) -> bool:

        try:

            ticker = self._request(symbol)

            if ticker is None:

                return False

            info = ticker.fast_info

            return len(info) > 0

        except Exception:

            return False

    # =====================================================
    # Current Price
    # =====================================================

    @timer
    @cached(ttl=20)

    def get_price(self, symbol: str) -> dict[str, Any]:

        """
        Current stock price.
        """

        ticker = self._request(symbol)

        if ticker is None:

            return {}

        try:

            info = ticker.fast_info

            return {

                "symbol": symbol,

                "price":
                    info.get("lastPrice"),

                "open":
                    info.get("open"),

                "high":
                    info.get("dayHigh"),

                "low":
                    info.get("dayLow"),

                "volume":
                    info.get("lastVolume"),

                "market_cap":
                    info.get("marketCap"),

                "currency":
                    info.get("currency"),

            }

        except Exception as e:

            logger.exception(e)

            return {}
```
```python
    # =====================================================
    # Historical Data
    # =====================================================

    @timer
    @cached(ttl=300)
    def get_history(
        self,
        symbol: str,
        period: str = "6mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        جلب البيانات التاريخية للسهم.

        Parameters
        ----------
        symbol : رمز السهم
        period : الفترة (1d,5d,1mo,3mo,6mo,1y,2y,5y,max)
        interval : الفاصل الزمني (1m,5m,15m,1h,1d,1wk)

        Returns
        -------
        DataFrame
        """

        ticker = self._request(symbol)

        if ticker is None:
            return pd.DataFrame()

        try:

            df = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=True
            )

            if df.empty:
                logger.warning(f"No history found for {symbol}")
                return pd.DataFrame()

            df.reset_index(inplace=True)

            logger.info(
                f"{symbol} history loaded ({len(df)} rows)"
            )

            return df

        except Exception as e:

            logger.exception(e)

            return pd.DataFrame()
```

