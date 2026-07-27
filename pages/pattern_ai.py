import numpy as np
import pandas as pd
from scipy.signal import find_peaks


class PatternAI:

    def __init__(self):
        pass

    def detect_double_top(self, df):
        peaks, _ = find_peaks(df["Close"], distance=10)

        if len(peaks) < 2:
            return False

        p1 = df["Close"].iloc[peaks[-2]]
        p2 = df["Close"].iloc[peaks[-1]]

        diff = abs(p1 - p2) / p1

        return diff < 0.03

    def detect_double_bottom(self, df):
        lows, _ = find_peaks(-df["Close"], distance=10)

        if len(lows) < 2:
            return False

        b1 = df["Close"].iloc[lows[-2]]
        b2 = df["Close"].iloc[lows[-1]]

        diff = abs(b1 - b2) / b1

        return diff < 0.03

    def detect_triangle(self, df):

        highs = df["High"].tail(30)
        lows = df["Low"].tail(30)

        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]

        if high_slope < 0 and low_slope > 0:
            return "Symmetrical Triangle"

        return None

    def detect_channel(self, df):

        highs = df["High"].tail(50)
        lows = df["Low"].tail(50)

        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]

        if abs(high_slope - low_slope) < 0.05:
            return True

        return False

    def detect_flag(self, df):

        move = (
            df["Close"].iloc[-20]
            - df["Close"].iloc[-40]
        ) / df["Close"].iloc[-40]

        consolidation = (
            df["High"].tail(15).max()
            - df["Low"].tail(15).min()
        ) / df["Close"].iloc[-1]

        if move > 0.15 and consolidation < 0.05:
            return True

        return False

    def scan_all(self, df):

        patterns = []

        if self.detect_double_top(df):
            patterns.append("Double Top")

        if self.detect_double_bottom(df):
            patterns.append("Double Bottom")

        triangle = self.detect_triangle(df)
        if triangle:
            patterns.append(triangle)

        if self.detect_channel(df):
            patterns.append("Price Channel")

        if self.detect_flag(df):
            patterns.append("Bull Flag")

        return patterns
