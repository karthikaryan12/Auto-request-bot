# ==========================================
# 📦 SUPPLY & DEMAND ZONE ENGINE
# SMC / Mentor Strategy Upgrade
# ==========================================
# Supply Zone  = area where price dropped sharply from (sellers dominate)
#   → Price returns → sellers re-enter → short entry zone
#
# Demand Zone  = area where price rallied sharply from (buyers dominate)
#   → Price returns → buyers re-enter → long entry zone
#
# Zone is VALID until price closes through it (broken/mitigated).
# Stronger zones = larger / faster departure from the zone.
# ==========================================

import numpy as np


def detect_supply_demand(df, max_lookback=60):
    """
    Identifies Supply and Demand zones from last `max_lookback` candles.
    Returns nearest valid demand (buy) and supply (sell) zones.
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

    demand_zones = []
    supply_zones = []

    n        = len(df)
    lookback = min(max_lookback, n - 5)

    for i in range(lookback, 3, -1):
        base     = df.iloc[-(i + 1)]
        b_open   = float(base["open"])
        b_close  = float(base["close"])
        b_high   = float(base["high"])
        b_low    = float(base["low"])
        b_body   = abs(b_close - b_open)

        # Departure move: next 3 candles
        departure = df.iloc[-i: -(i - 3) if (i - 3) > 0 else n]
        if len(departure) < 2:
            continue

        dep_high  = departure["high"].max()
        dep_low   = departure["low"].min()
        dep_range = dep_high - dep_low

        # ----------------------------------
        # DEMAND ZONE (base + strong bullish departure)
        # Base candle is small (consolidation) OR bearish
        # followed by a big bullish impulse
        # ----------------------------------
        bullish_departure = (
            dep_high > b_high + atr * 0.8 and
            dep_range > avg_body * 2.0
        )
        small_base = b_body <= avg_body * 1.2

        if bullish_departure and small_base:
            zone_top    = max(b_open, b_close)
            zone_bottom = b_low
            zone_mid    = (zone_top + zone_bottom) / 2.0

            # Mitigated if price has closed BELOW the zone bottom
            subsequent  = df.iloc[-i:]
            mitigated   = subsequent["close"].min() < zone_bottom

            if not mitigated and zone_bottom < price:
                strength = round(dep_range / atr, 2)
                demand_zones.append({
                    "top":       round(zone_top, 2),
                    "bottom":    round(zone_bottom, 2),
                    "mid":       round(zone_mid, 2),
                    "age":       i,
                    "mitigated": False,
                    "type":      "DEMAND",
                    "strength":  strength
                })

        # ----------------------------------
        # SUPPLY ZONE (base + strong bearish departure)
        # Base candle is small (consolidation) OR bullish
        # followed by a big bearish impulse
        # ----------------------------------
        bearish_departure = (
            dep_low < b_low - atr * 0.8 and
            dep_range > avg_body * 2.0
        )

        if bearish_departure and small_base:
            zone_top    = b_high
            zone_bottom = min(b_open, b_close)
            zone_mid    = (zone_top + zone_bottom) / 2.0

            subsequent  = df.iloc[-i:]
            mitigated   = subsequent["close"].max() > zone_top

            if not mitigated and zone_top > price:
                strength = round(dep_range / atr, 2)
                supply_zones.append({
                    "top":       round(zone_top, 2),
                    "bottom":    round(zone_bottom, 2),
                    "mid":       round(zone_mid, 2),
                    "age":       i,
                    "mitigated": False,
                    "type":      "SUPPLY",
                    "strength":  strength
                })

    # ----------------------------------
    # Sort: strongest + nearest first
    # ----------------------------------
    demand_zones.sort(key=lambda x: (-x["strength"], abs(price - x["mid"])))
    supply_zones.sort(key=lambda x: (-x["strength"], abs(price - x["mid"])))

    nearest_demand = demand_zones[0] if demand_zones else None
    nearest_supply = supply_zones[0] if supply_zones else None

    # ----------------------------------
    # Is price AT a zone right now?
    # ----------------------------------
    in_demand = False
    in_supply = False

    if nearest_demand:
        in_demand = nearest_demand["bottom"] <= price <= nearest_demand["top"]

    if nearest_supply:
        in_supply = nearest_supply["bottom"] <= price <= nearest_supply["top"]

    # ----------------------------------
    # Bias
    # ----------------------------------
    sd_bias = "NEUTRAL"
    dist_dem = abs(price - nearest_demand["mid"]) if nearest_demand else 999999
    dist_sup = abs(price - nearest_supply["mid"]) if nearest_supply else 999999

    if in_demand:
        sd_bias = "BULLISH"
    elif in_supply:
        sd_bias = "BEARISH"
    elif dist_dem < dist_sup:
        sd_bias = "BULLISH"
    elif dist_sup < dist_dem:
        sd_bias = "BEARISH"

    # ----------------------------------
    # Score
    # ----------------------------------
    score = 0
    if in_demand or in_supply:
        score = 85
    elif dist_dem < atr * 2 or dist_sup < atr * 2:
        score = 55
    elif dist_dem < atr * 4 or dist_sup < atr * 4:
        score = 35

    return {
        "demand_zone":   nearest_demand,
        "supply_zone":   nearest_supply,
        "all_demand":    demand_zones,
        "all_supply":    supply_zones,
        "in_demand":     in_demand,
        "in_supply":     in_supply,
        "sd_bias":       sd_bias,
        "score":         score,
        "zone_count":    len(demand_zones) + len(supply_zones)
    }


def _empty():
    return {
        "demand_zone":  None,
        "supply_zone":  None,
        "all_demand":   [],
        "all_supply":   [],
        "in_demand":    False,
        "in_supply":    False,
        "sd_bias":      "NEUTRAL",
        "score":        0,
        "zone_count":   0
    }
