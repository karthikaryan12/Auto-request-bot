# ==========================================
# 📐 FVG ENGINE (Fair Value Gap / Imbalance)
# SMC / Mentor Strategy Upgrade
# ==========================================
# A Fair Value Gap is a 3-candle pattern:
#   Bullish FVG: candle[1].low > candle[-1].high  → gap left unfilled above
#   Bearish FVG: candle[1].high < candle[-1].low  → gap left unfilled below
# Price tends to return and fill FVGs before continuing.
# We use UNFILLED FVGs as high-probability entry zones.
# ==========================================

import numpy as np


def detect_fvg(df, max_lookback=30):
    """
    Detects all unfilled Fair Value Gaps in the last `max_lookback` candles.
    Returns the nearest bullish and bearish FVG to current price.
    """
    if df is None or len(df) < 5:
        return _empty()

    price = float(df["close"].iloc[-1])
    atr   = (df["high"] - df["low"]).rolling(14).mean().iloc[-1]
    if np.isnan(atr) or atr <= 0:
        atr = (df["high"] - df["low"]).tail(10).mean()
    if atr <= 0:
        atr = 1.0

    bullish_fvgs = []
    bearish_fvgs = []

    n = len(df)
    lookback = min(max_lookback, n - 3)

    for i in range(lookback, 0, -1):
        c1 = df.iloc[-(i + 2)]
        c3 = df.iloc[-i]

        # ----------------------------------
        # Bullish FVG: gap between c1.high and c3.low
        # c3.low > c1.high  →  price moved up leaving a gap below
        # ----------------------------------
        if c3["low"] > c1["high"]:
            top    = float(c3["low"])
            bottom = float(c1["high"])
            mid    = (top + bottom) / 2.0
            size   = top - bottom

            # Check if already filled (price has traded through it)
            filled = df["low"].iloc[-i:].min() <= bottom
            if not filled:
                bullish_fvgs.append({
                    "top":    round(top, 2),
                    "bottom": round(bottom, 2),
                    "mid":    round(mid, 2),
                    "size":   round(size, 2),
                    "age":    i,
                    "filled": False,
                    "type":   "BULLISH"
                })

        # ----------------------------------
        # Bearish FVG: gap between c1.low and c3.high
        # c3.high < c1.low  →  price moved down leaving a gap above
        # ----------------------------------
        if c3["high"] < c1["low"]:
            top    = float(c1["low"])
            bottom = float(c3["high"])
            mid    = (top + bottom) / 2.0
            size   = top - bottom

            filled = df["high"].iloc[-i:].max() >= top
            if not filled:
                bearish_fvgs.append({
                    "top":    round(top, 2),
                    "bottom": round(bottom, 2),
                    "mid":    round(mid, 2),
                    "size":   round(size, 2),
                    "age":    i,
                    "filled": False,
                    "type":   "BEARISH"
                })

    # ----------------------------------
    # Nearest unfilled FVG to price
    # ----------------------------------
    nearest_bullish = None
    nearest_bearish = None

    if bullish_fvgs:
        bullish_fvgs.sort(key=lambda x: abs(price - x["mid"]))
        nearest_bullish = bullish_fvgs[0]

    if bearish_fvgs:
        bearish_fvgs.sort(key=lambda x: abs(price - x["mid"]))
        nearest_bearish = bearish_fvgs[0]

    # ----------------------------------
    # Is price INSIDE an FVG right now?
    # ----------------------------------
    in_bullish_fvg = False
    in_bearish_fvg = False

    if nearest_bullish:
        in_bullish_fvg = (
            nearest_bullish["bottom"] <= price <= nearest_bullish["top"]
        )

    if nearest_bearish:
        in_bearish_fvg = (
            nearest_bearish["bottom"] <= price <= nearest_bearish["top"]
        )

    # ----------------------------------
    # FVG Bias — which side is price approaching?
    # ----------------------------------
    fvg_bias = "NEUTRAL"
    dist_bull = abs(price - nearest_bullish["mid"]) if nearest_bullish else 999999
    dist_bear = abs(price - nearest_bearish["mid"]) if nearest_bearish else 999999

    if in_bullish_fvg:
        fvg_bias = "BULLISH"
    elif in_bearish_fvg:
        fvg_bias = "BEARISH"
    elif dist_bull < dist_bear:
        fvg_bias = "BULLISH"
    elif dist_bear < dist_bull:
        fvg_bias = "BEARISH"

    # ----------------------------------
    # Score
    # ----------------------------------
    score = 0
    if nearest_bullish:
        score += min(40, int(10 * nearest_bullish["size"] / atr))
    if nearest_bearish:
        score += min(40, int(10 * nearest_bearish["size"] / atr))
    if in_bullish_fvg or in_bearish_fvg:
        score += 30
    score = min(score, 100)

    return {
        "bullish_fvg":     nearest_bullish,
        "bearish_fvg":     nearest_bearish,
        "all_bullish_fvgs": bullish_fvgs,
        "all_bearish_fvgs": bearish_fvgs,
        "in_bullish_fvg":  in_bullish_fvg,
        "in_bearish_fvg":  in_bearish_fvg,
        "fvg_bias":        fvg_bias,
        "score":           score,
        "fvg_count":       len(bullish_fvgs) + len(bearish_fvgs)
    }


def _empty():
    return {
        "bullish_fvg":      None,
        "bearish_fvg":      None,
        "all_bullish_fvgs": [],
        "all_bearish_fvgs": [],
        "in_bullish_fvg":   False,
        "in_bearish_fvg":   False,
        "fvg_bias":         "NEUTRAL",
        "score":            0,
        "fvg_count":        0
    }
