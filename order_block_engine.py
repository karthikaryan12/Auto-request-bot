# ==========================================
# 🏦 ORDER BLOCK ENGINE
# SMC / Mentor Strategy Upgrade
# ==========================================
# Order Block (OB) = last opposing candle before a BOS / impulse move.
#
# Bullish OB: Last BEARISH candle before a strong bullish BOS
#   → Price returns here → institutions buy again → long entry zone
#
# Bearish OB: Last BULLISH candle before a strong bearish BOS
#   → Price returns here → institutions sell again → short entry zone
#
# Mitigation = price has revisited the OB zone
# Once mitigated, OB loses its significance
# ==========================================

import numpy as np


def detect_order_blocks(df, max_lookback=50):
    """
    Scans last `max_lookback` candles for valid Order Blocks.
    Returns nearest bullish OB (demand) and bearish OB (supply) to price.
    """
    if df is None or len(df) < 10:
        return _empty()

    price = float(df["close"].iloc[-1])
    atr   = (df["high"] - df["low"]).rolling(14).mean().iloc[-1]
    if np.isnan(atr) or atr <= 0:
        atr = (df["high"] - df["low"]).tail(10).mean()
    if atr <= 0:
        atr = 1.0

    avg_body = abs(df["close"] - df["open"]).tail(20).mean()

    bullish_obs = []
    bearish_obs = []

    n       = len(df)
    lookback = min(max_lookback, n - 4)

    for i in range(lookback, 2, -1):
        candle  = df.iloc[-(i + 1)]
        c_body  = abs(float(candle["close"]) - float(candle["open"]))

        # Next 3 candles after this candle
        following = df.iloc[-i: -(i - 3) if (i - 3) > 0 else n]

        if len(following) < 2:
            continue

        # Displacement check: following candles move strongly away
        fwd_high = following["high"].max()
        fwd_low  = following["low"].min()
        fwd_move = fwd_high - fwd_low

        # ----------------------------------
        # Bullish OB: bearish candle (red) before a bullish impulse
        # ----------------------------------
        is_bearish_candle = float(candle["close"]) < float(candle["open"])
        bullish_displacement = (
            fwd_high > float(candle["high"]) + atr * 0.5 and
            fwd_move > avg_body * 1.5
        )

        if is_bearish_candle and bullish_displacement and c_body > avg_body * 0.5:
            ob_top    = float(candle["high"])
            ob_bottom = float(candle["low"])
            ob_mid    = (ob_top + ob_bottom) / 2.0

            # Mitigated if price has already traded INTO the OB zone
            subsequent = df.iloc[-i:]
            mitigated  = subsequent["low"].min() <= ob_top

            if not mitigated:
                bullish_obs.append({
                    "top":       round(ob_top, 2),
                    "bottom":    round(ob_bottom, 2),
                    "mid":       round(ob_mid, 2),
                    "age":       i,
                    "mitigated": False,
                    "type":      "BULLISH_OB",
                    "strength":  round(fwd_move / atr, 2)
                })

        # ----------------------------------
        # Bearish OB: bullish candle (green) before a bearish impulse
        # ----------------------------------
        is_bullish_candle = float(candle["close"]) > float(candle["open"])
        bearish_displacement = (
            fwd_low < float(candle["low"]) - atr * 0.5 and
            fwd_move > avg_body * 1.5
        )

        if is_bullish_candle and bearish_displacement and c_body > avg_body * 0.5:
            ob_top    = float(candle["high"])
            ob_bottom = float(candle["low"])
            ob_mid    = (ob_top + ob_bottom) / 2.0

            subsequent = df.iloc[-i:]
            mitigated  = subsequent["high"].max() >= ob_bottom

            if not mitigated:
                bearish_obs.append({
                    "top":       round(ob_top, 2),
                    "bottom":    round(ob_bottom, 2),
                    "mid":       round(ob_mid, 2),
                    "age":       i,
                    "mitigated": False,
                    "type":      "BEARISH_OB",
                    "strength":  round(fwd_move / atr, 2)
                })

    # ----------------------------------
    # Sort by strength then proximity
    # ----------------------------------
    bullish_obs.sort(key=lambda x: (-x["strength"], abs(price - x["mid"])))
    bearish_obs.sort(key=lambda x: (-x["strength"], abs(price - x["mid"])))

    nearest_bullish_ob = bullish_obs[0] if bullish_obs else None
    nearest_bearish_ob = bearish_obs[0] if bearish_obs else None

    # ----------------------------------
    # Is price currently INSIDE an OB?
    # ----------------------------------
    in_bullish_ob = False
    in_bearish_ob = False

    if nearest_bullish_ob:
        in_bullish_ob = (
            nearest_bullish_ob["bottom"] <= price <= nearest_bullish_ob["top"]
        )

    if nearest_bearish_ob:
        in_bearish_ob = (
            nearest_bearish_ob["bottom"] <= price <= nearest_bearish_ob["top"]
        )

    # ----------------------------------
    # OB Bias
    # ----------------------------------
    ob_bias = "NEUTRAL"
    dist_bull = abs(price - nearest_bullish_ob["mid"]) if nearest_bullish_ob else 999999
    dist_bear = abs(price - nearest_bearish_ob["mid"]) if nearest_bearish_ob else 999999

    if in_bullish_ob:
        ob_bias = "BULLISH"
    elif in_bearish_ob:
        ob_bias = "BEARISH"
    elif dist_bull < dist_bear:
        ob_bias = "BULLISH"
    elif dist_bear < dist_bull:
        ob_bias = "BEARISH"

    # ----------------------------------
    # Score — higher if price is AT an OB
    # ----------------------------------
    score = 0
    if in_bullish_ob or in_bearish_ob:
        score = 80
    elif dist_bull < atr * 2 or dist_bear < atr * 2:
        score = 50
    elif dist_bull < atr * 4 or dist_bear < atr * 4:
        score = 30

    return {
        "bullish_ob":       nearest_bullish_ob,
        "bearish_ob":       nearest_bearish_ob,
        "all_bullish_obs":  bullish_obs,
        "all_bearish_obs":  bearish_obs,
        "in_bullish_ob":    in_bullish_ob,
        "in_bearish_ob":    in_bearish_ob,
        "ob_bias":          ob_bias,
        "score":            score,
        "ob_count":         len(bullish_obs) + len(bearish_obs)
    }


def _empty():
    return {
        "bullish_ob":      None,
        "bearish_ob":      None,
        "all_bullish_obs": [],
        "all_bearish_obs": [],
        "in_bullish_ob":   False,
        "in_bearish_ob":   False,
        "ob_bias":         "NEUTRAL",
        "score":           0,
        "ob_count":        0
    }
