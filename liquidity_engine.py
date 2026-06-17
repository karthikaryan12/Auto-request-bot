# ==========================================
# 💧 LIQUIDITY MASTER ENGINE
# ==========================================

import numpy as np


def liquidity_master(df):

    highs = df["high"].tail(50).values
    lows = df["low"].tail(50).values

    close = df["close"].iloc[-1]

    # --------------------------------------
    # ATR
    # --------------------------------------
    atr = (
        df["high"] -
        df["low"]
    ).rolling(14).mean().iloc[-1]

    if np.isnan(atr):
        atr = np.mean(highs - lows)

    tolerance = max(
        close * 0.001,
        atr * 0.25
    )

    high_clusters = []
    low_clusters = []

    # --------------------------------------
    # CLUSTER DETECTION
    # --------------------------------------
    for i in range(len(highs)):

        cluster_h = [
            h for h in highs
            if abs(h - highs[i]) <= tolerance
        ]

        if len(cluster_h) >= 4:

            level = round(
                np.mean(cluster_h),
                2
            )

            if not any(
                abs(level - x) <= tolerance
                for x in high_clusters
            ):
                high_clusters.append(level)

        cluster_l = [
            l for l in lows
            if abs(l - lows[i]) <= tolerance
        ]

        if len(cluster_l) >= 4:

            level = round(
                np.mean(cluster_l),
                2
            )

            if not any(
                abs(level - x) <= tolerance
                for x in low_clusters
            ):
                low_clusters.append(level)

    # --------------------------------------
    # LIQUIDITY LEVELS
    # --------------------------------------
    buy_liq = (
        max(high_clusters)
        if high_clusters
        else np.max(highs)
    )

    sell_liq = (
        min(low_clusters)
        if low_clusters
        else np.min(lows)
    )

    # --------------------------------------
    # STRENGTH
    # --------------------------------------
    buy_strength = sum(
        abs(h - buy_liq) <= tolerance
        for h in highs
    )

    sell_strength = sum(
        abs(l - sell_liq) <= tolerance
        for l in lows
    )

    # --------------------------------------
    # SWEEP DETECTION
    # --------------------------------------
    last_high = highs[-1]
    last_low = lows[-1]

    prev_high = max(highs[:-2])
    prev_low = min(lows[:-2])

    buy_sweep = (
        last_high > prev_high + tolerance * 0.3
        and
        close < last_high
    )

    sell_sweep = (
        last_low < prev_low - tolerance * 0.3
        and
        close > last_low
    )

    # --------------------------------------
    # REJECTION
    # --------------------------------------
    rejection_up = (
        last_high > buy_liq
        and
        close < buy_liq
    )

    rejection_down = (
        last_low < sell_liq
        and
        close > sell_liq
    )

    # --------------------------------------
    # DISTANCE
    # --------------------------------------
    dist_to_buy = abs(close - buy_liq)
    dist_to_sell = abs(close - sell_liq)

    near_buy = dist_to_buy <= tolerance
    near_sell = dist_to_sell <= tolerance

    # --------------------------------------
    # LIQUIDITY BIAS
    # --------------------------------------
    bias = "NEUTRAL"

    if dist_to_sell < dist_to_buy:
        bias = "BULLISH"

    elif dist_to_buy < dist_to_sell:
        bias = "BEARISH"

    # --------------------------------------
    # TARGET LOGIC
    # --------------------------------------
    target = "NONE"
    expected_move = "NEUTRAL"

    if dist_to_buy < dist_to_sell:
        target = "BUY SIDE"
        expected_move = "BEARISH"

    elif dist_to_sell < dist_to_buy:
        target = "SELL SIDE"
        expected_move = "BULLISH"

    # Sweep override
    if buy_sweep:
        expected_move = "BEARISH"

    if sell_sweep:
        expected_move = "BULLISH"

    # Rejection override
    if rejection_up:
        expected_move = "BEARISH"

    if rejection_down:
        expected_move = "BULLISH"

    # --------------------------------------
    # SCORE
    # --------------------------------------
    score = 40

    score += min(buy_strength, 5) * 3
    score += min(sell_strength, 5) * 3

    if near_buy or near_sell:
        score += 10

    if buy_sweep or sell_sweep:
        score += 20

    if rejection_up or rejection_down:
        score += 20

    score = max(0, min(score, 100))

    # --------------------------------------
    # INDUCEMENT DETECTION
    # A small liquidity grab (fake sweep) used to lure retail
    # traders in the wrong direction before the real move.
    # Pattern: minor swing broken → price quickly reverses
    # Inducement = sweep of a SMALL swing, not the major level
    # --------------------------------------
    inducement_bullish = False
    inducement_bearish = False

    if len(highs) >= 6 and len(lows) >= 6:
        # Minor swing levels (last 5 candles vs next 5 candles)
        minor_high = max(highs[-6:-3])
        minor_low  = min(lows[-6:-3])

        # Bullish inducement: price briefly swept below minor low
        # then closed back above it (fake sell → real buy coming)
        if (last_low < minor_low - tolerance * 0.2 and
                close > minor_low):
            inducement_bullish = True
            score = min(score + 15, 100)

        # Bearish inducement: price briefly swept above minor high
        # then closed back below it (fake buy → real sell coming)
        if (last_high > minor_high + tolerance * 0.2 and
                close < minor_high):
            inducement_bearish = True
            score = min(score + 15, 100)

    if inducement_bullish or inducement_bearish:
        if buy_sweep or sell_sweep:
            state_inducement = "INDUCEMENT+SWEEP"
        else:
            state_inducement = "INDUCEMENT"
    else:
        state_inducement = "NONE"

    # --------------------------------------
    # LIQUIDITY STATE
    # --------------------------------------
    if buy_sweep or sell_sweep:
        state = "SWEEP"
    elif rejection_up or rejection_down:
        state = "REJECTION"
    elif near_buy or near_sell:
        state = "NEAR_LIQUIDITY"
    elif score >= 70:
        state = "ACTIVE"
    else:
        state = "INACTIVE"

    # --------------------------------------
    # FINAL
    # --------------------------------------
    nearest = (
        "BUY"
        if dist_to_buy < dist_to_sell
        else "SELL"
    )

    return {

        "buy_liq": round(buy_liq, 2),
        "sell_liq": round(sell_liq, 2),

        "buy_strength": int(buy_strength),
        "sell_strength": int(sell_strength),

        "buy_sweep": buy_sweep,
        "sell_sweep": sell_sweep,

        "near_buy_liquidity": near_buy,
        "near_sell_liquidity": near_sell,

        "target": target,
        "expected_move": expected_move,

        "nearest_liquidity": nearest,

        "liquidity_score": score,
        "liquidity_bias": bias,
        "state": state,
        "liquidity_sweep": buy_sweep or sell_sweep,
        "near_liquidity": near_buy or near_sell,
        "inducement_bullish": inducement_bullish,
        "inducement_bearish": inducement_bearish,
        "inducement_state":   state_inducement
    }

def liquidity_engine(df):
    return liquidity_master(df)
