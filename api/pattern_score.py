import pandas as pd


def pattern_score(df, patterns):

    score = 0

    volume = df["Volume"].iloc[-1]
    avg_volume = df["Volume"].tail(20).mean()

    if volume > avg_volume:
        score += 20

    if "Bull Flag" in patterns:
        score += 30

    if "Symmetrical Triangle" in patterns:
        score += 25

    if "Double Bottom" in patterns:
        score += 25

    rsi = df["RSI"].iloc[-1]

    if 50 < rsi < 70:
        score += 15

    return min(score, 100)
