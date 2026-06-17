# ==========================================
# 🏦 INSTITUTIONAL PRICE ACTION SYSTEM
# ==========================================
# Predictive Setup Engine
# Identifies key levels, zones, and generates
# CONDITIONAL trade setups for future moves
# (not reactive signals after the move)
# ==========================================

import numpy as np
import pandas as pd


class InstitutionalPriceActionSystem:
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol

    # ==========================================
    # SWING HIGH / LOW DETECTION
    # ==========================================
    def find_swings(self, df, lookback=5):
        """Find swing highs and swing lows"""
        if df is None or len(df) < lookback * 2 + 1:
            return [], []

        highs = df["high"].values
        lows = df["low"].values
        swing_highs = []
        swing_lows = []

        for i in range(lookback, len(df) - lookback):
            # Swing high: highest in window
            if highs[i] == max(highs[i - lookback:i + lookback + 1]):
                swing_highs.append(i)
            # Swing low: lowest in window
            if lows[i] == min(lows[i - lookback:i + lookback + 1]):
                swing_lows.append(i)

        return swing_highs, swing_lows

    # ==========================================
    # MARKET STRUCTURE (HTF)
    # ==========================================
    def detect_market_structure(self, df):
        """Detect HTF trend using swing structure"""
        if df is None or len(df) < 30:
            return "NEUTRAL", "NO_DATA"

        swing_highs, swing_lows = self.find_swings(df, lookback=3)

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return "NEUTRAL", "INSUFFICIENT_SWINGS"

        highs = df["high"].values
        lows = df["low"].values

        # Check last 2 swing highs and lows
        last_sh = highs[swing_highs[-1]]
        prev_sh = highs[swing_highs[-2]]
        last_sl = lows[swing_lows[-1]]
        prev_sl = lows[swing_lows[-2]]

        # Higher highs + higher lows = bullish
        if last_sh > prev_sh and last_sl > prev_sl:
            return "BULLISH", "HH_HL"

        # Lower highs + lower lows = bearish
        elif last_sh < prev_sh and last_sl < prev_sl:
            return "BEARISH", "LH_LL"

        # Higher high but lower low = range/expansion
        elif last_sh > prev_sh and last_sl < prev_sl:
            return "NEUTRAL", "EXPANSION"

        # Lower high but higher low = compression
        elif last_sh < prev_sh and last_sl > prev_sl:
            return "NEUTRAL", "COMPRESSION"

        return "NEUTRAL", "MIXED"

    # ==========================================
    # SUPPLY ZONE DETECTION (15m)
    # ==========================================
    def find_supply_zone(self, df, lookback=50):
        """Find the most recent supply zone (bearish order block)
        Supply = last bullish candle before a strong bearish move"""
        if df is None or len(df) < lookback:
            return None

        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        closes = df["close"].values

        best_zone = None
        best_strength = 0

        for i in range(len(df) - 3, max(len(df) - lookback, 2), -1):
            # Look for bullish candle followed by strong bearish move
            is_bullish = closes[i] > opens[i]
            if not is_bullish:
                continue

            # Check if next candles are strongly bearish
            if i + 2 >= len(df):
                continue

            drop_after = highs[i] - min(lows[i+1], lows[min(i+2, len(df)-1)])
            avg_range = np.mean(highs[max(0, i-10):i] - lows[max(0, i-10):i])

            if avg_range == 0:
                continue

            # Strong drop = 2x average range
            strength = drop_after / avg_range
            if strength >= 1.5 and strength > best_strength:
                zone_high = highs[i]
                zone_low = min(opens[i], closes[i])
                best_zone = (zone_low, zone_high, strength)
                best_strength = strength

        return best_zone

    # ==========================================
    # DEMAND ZONE DETECTION (15m)
    # ==========================================
    def find_demand_zone(self, df, lookback=50):
        """Find the most recent demand zone (bullish order block)
        Demand = last bearish candle before a strong bullish move"""
        if df is None or len(df) < lookback:
            return None

        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        closes = df["close"].values

        best_zone = None
        best_strength = 0

        for i in range(len(df) - 3, max(len(df) - lookback, 2), -1):
            # Look for bearish candle followed by strong bullish move
            is_bearish = closes[i] < opens[i]
            if not is_bearish:
                continue

            # Check if next candles are strongly bullish
            if i + 2 >= len(df):
                continue

            rise_after = max(highs[i+1], highs[min(i+2, len(df)-1)]) - lows[i]
            avg_range = np.mean(highs[max(0, i-10):i] - lows[max(0, i-10):i])

            if avg_range == 0:
                continue

            # Strong rise = 2x average range
            strength = rise_after / avg_range
            if strength >= 1.5 and strength > best_strength:
                zone_high = max(opens[i], closes[i])
                zone_low = lows[i]
                best_zone = (zone_low, zone_high, strength)
                best_strength = strength

        return best_zone

    # ==========================================
    # LIQUIDITY SWEEP DETECTION
    # ==========================================
    def detect_liquidity_sweep_buy_side(self, df, lookback=20):
        """Detect buy-side liquidity sweep (price spikes above high then reverses)
        This is MANDATORY for SELL setups"""
        if df is None or len(df) < lookback + 5:
            return False, 0

        highs = df["high"].values
        closes = df["close"].values

        # Find the highest high in recent history (excluding last 3 candles)
        recent_high = max(highs[-lookback-3:-3])

        # Check if any of last 3 candles spiked above then closed below
        for i in range(-3, 0):
            if highs[i] > recent_high and closes[i] < recent_high:
                return True, recent_high

        return False, recent_high

    def detect_liquidity_sweep_sell_side(self, df, lookback=20):
        """Detect sell-side liquidity sweep (price spikes below low then reverses)
        This is MANDATORY for BUY setups"""
        if df is None or len(df) < lookback + 5:
            return False, 0

        lows = df["low"].values
        closes = df["close"].values

        # Find the lowest low in recent history (excluding last 3 candles)
        recent_low = min(lows[-lookback-3:-3])

        # Check if any of last 3 candles spiked below then closed above
        for i in range(-3, 0):
            if lows[i] < recent_low and closes[i] > recent_low:
                return True, recent_low

        return False, recent_low

    # ==========================================
    # BOS (Break of Structure)
    # ==========================================
    def detect_bos_bullish(self, df, lookback=20):
        """Detect bullish BOS — price breaks above recent swing high"""
        if df is None or len(df) < lookback:
            return False, 0

        swing_highs, _ = self.find_swings(df, lookback=3)
        if len(swing_highs) < 2:
            return False, 0

        last_sh_level = df["high"].values[swing_highs[-2]]
        current_close = df["close"].values[-1]

        if current_close > last_sh_level:
            return True, last_sh_level

        return False, last_sh_level

    def detect_bos_bearish(self, df, lookback=20):
        """Detect bearish BOS — price breaks below recent swing low"""
        if df is None or len(df) < lookback:
            return False, 0

        _, swing_lows = self.find_swings(df, lookback=3)
        if len(swing_lows) < 2:
            return False, 0

        last_sl_level = df["low"].values[swing_lows[-2]]
        current_close = df["close"].values[-1]

        if current_close < last_sl_level:
            return True, last_sl_level

        return False, last_sl_level

    # ==========================================
    # CHOCH (Change of Character)
    # ==========================================
    def detect_choch_bullish(self, df):
        """Detect bullish CHOCH — in a downtrend, price breaks above last lower high"""
        if df is None or len(df) < 30:
            return False, 0

        swing_highs, swing_lows = self.find_swings(df, lookback=3)
        if len(swing_highs) < 3 or len(swing_lows) < 2:
            return False, 0

        highs = df["high"].values
        lows = df["low"].values

        # Check if previous structure was bearish (lower highs)
        sh1 = highs[swing_highs[-3]]
        sh2 = highs[swing_highs[-2]]
        was_bearish = sh2 < sh1

        # Current price breaks above the last lower high
        last_lh = highs[swing_highs[-2]]
        current_close = df["close"].values[-1]

        if was_bearish and current_close > last_lh:
            return True, last_lh

        return False, last_lh if len(swing_highs) >= 2 else 0

    def detect_choch_bearish(self, df):
        """Detect bearish CHOCH — in an uptrend, price breaks below last higher low"""
        if df is None or len(df) < 30:
            return False, 0

        swing_highs, swing_lows = self.find_swings(df, lookback=3)
        if len(swing_highs) < 2 or len(swing_lows) < 3:
            return False, 0

        lows = df["low"].values

        # Check if previous structure was bullish (higher lows)
        sl1 = lows[swing_lows[-3]]
        sl2 = lows[swing_lows[-2]]
        was_bullish = sl2 > sl1

        # Current price breaks below the last higher low
        last_hl = lows[swing_lows[-2]]
        current_close = df["close"].values[-1]

        if was_bullish and current_close < last_hl:
            return True, last_hl

        return False, last_hl if len(swing_lows) >= 2 else 0

    # ==========================================
    # CONFIRMATION CANDLE DETECTION
    # ==========================================
    def detect_bearish_confirmation(self, df):
        """Detect bearish confirmation: engulfing or pin bar at supply"""
        if df is None or len(df) < 3:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        body = abs(last["close"] - last["open"])
        upper_wick = last["high"] - max(last["close"], last["open"])
        lower_wick = min(last["close"], last["open"]) - last["low"]
        total_range = last["high"] - last["low"]

        if total_range == 0:
            return None

        # Bearish engulfing
        if (last["close"] < last["open"] and
            prev["close"] > prev["open"] and
            last["open"] >= prev["close"] and
            last["close"] <= prev["open"]):
            return "BEARISH_ENGULFING"

        # Bearish pin bar (long upper wick)
        if upper_wick > body * 2 and upper_wick > total_range * 0.6:
            return "BEARISH_PIN_BAR"

        # Bearish strong candle (big body, small wicks)
        if (last["close"] < last["open"] and
            body > total_range * 0.7):
            return "BEARISH_MARUBOZU"

        return None

    def detect_bullish_confirmation(self, df):
        """Detect bullish confirmation: engulfing or pin bar at demand"""
        if df is None or len(df) < 3:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        body = abs(last["close"] - last["open"])
        upper_wick = last["high"] - max(last["close"], last["open"])
        lower_wick = min(last["close"], last["open"]) - last["low"]
        total_range = last["high"] - last["low"]

        if total_range == 0:
            return None

        # Bullish engulfing
        if (last["close"] > last["open"] and
            prev["close"] < prev["open"] and
            last["open"] <= prev["close"] and
            last["close"] >= prev["open"]):
            return "BULLISH_ENGULFING"

        # Bullish pin bar (long lower wick)
        if lower_wick > body * 2 and lower_wick > total_range * 0.6:
            return "BULLISH_PIN_BAR"

        # Bullish strong candle (big body, small wicks)
        if (last["close"] > last["open"] and
            body > total_range * 0.7):
            return "BULLISH_MARUBOZU"

        return None

    # ==========================================
    # CHANNEL DETECTION (Trendline-based)
    # ==========================================
    def detect_channel(self, df, lookback=50):
        """Detect ascending/descending/horizontal channels using swing points.
        Returns channel type, upper/lower trendline values at current bar,
        and price position within the channel (0=bottom, 1=top)."""
        if df is None or len(df) < lookback:
            return {
                "type": "NONE",
                "upper": 0,
                "lower": 0,
                "position": 0.5,
                "slope": 0,
                "strength": 0
            }

        swing_highs, swing_lows = self.find_swings(df, lookback=5)

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {
                "type": "NONE",
                "upper": 0,
                "lower": 0,
                "position": 0.5,
                "slope": 0,
                "strength": 0
            }

        highs = df["high"].values
        lows = df["low"].values
        n = len(df)

        # Use last few swing points to fit trendlines
        sh_indices = swing_highs[-min(5, len(swing_highs)):]
        sl_indices = swing_lows[-min(5, len(swing_lows)):]

        sh_x = np.array(sh_indices, dtype=float)
        sh_y = np.array([highs[i] for i in sh_indices], dtype=float)
        sl_x = np.array(sl_indices, dtype=float)
        sl_y = np.array([lows[i] for i in sl_indices], dtype=float)

        # Linear regression for upper trendline (swing highs)
        if len(sh_x) >= 2:
            upper_slope, upper_intercept = np.polyfit(sh_x, sh_y, 1)
        else:
            upper_slope, upper_intercept = 0, highs[-1]

        # Linear regression for lower trendline (swing lows)
        if len(sl_x) >= 2:
            lower_slope, lower_intercept = np.polyfit(sl_x, sl_y, 1)
        else:
            lower_slope, lower_intercept = 0, lows[-1]

        # Current trendline values
        current_idx = float(n - 1)
        upper_value = upper_slope * current_idx + upper_intercept
        lower_value = lower_slope * current_idx + lower_intercept

        # Channel width and position
        channel_width = upper_value - lower_value
        if channel_width <= 0:
            return {
                "type": "NONE",
                "upper": 0,
                "lower": 0,
                "position": 0.5,
                "slope": 0,
                "strength": 0
            }

        current_price = float(df["close"].iloc[-1])
        position = (current_price - lower_value) / channel_width
        position = max(0, min(1, position))

        # Average slope determines channel type
        avg_slope = (upper_slope + lower_slope) / 2
        avg_price = (upper_value + lower_value) / 2
        slope_pct = (avg_slope / avg_price) * 100 if avg_price > 0 else 0

        if slope_pct > 0.02:
            channel_type = "ASCENDING"
        elif slope_pct < -0.02:
            channel_type = "DESCENDING"
        else:
            channel_type = "HORIZONTAL"

        # Strength: how well prices respect the channel (R-squared proxy)
        touch_count = 0
        for i in sh_indices:
            expected = upper_slope * i + upper_intercept
            if abs(highs[i] - expected) < channel_width * 0.15:
                touch_count += 1
        for i in sl_indices:
            expected = lower_slope * i + lower_intercept
            if abs(lows[i] - expected) < channel_width * 0.15:
                touch_count += 1

        total_points = len(sh_indices) + len(sl_indices)
        strength = round((touch_count / total_points) * 100, 1) if total_points > 0 else 0

        return {
            "type": channel_type,
            "upper": round(upper_value, 2),
            "lower": round(lower_value, 2),
            "position": round(position, 3),
            "slope": round(slope_pct, 4),
            "strength": strength,
            "width": round(channel_width, 2)
        }

    # ==========================================
    # CANDLE MOMENTUM SCORE
    # ==========================================
    def candle_momentum_score(self, df, lookback=10):
        """Score candle momentum: body%, wick ratio, consecutive direction.
        Returns score -100 (strong bearish) to +100 (strong bullish)
        and metadata about candle character."""
        if df is None or len(df) < lookback:
            return {
                "score": 0,
                "consecutive_bullish": 0,
                "consecutive_bearish": 0,
                "avg_body_pct": 0,
                "last_candle_type": "NEUTRAL",
                "momentum_state": "NEUTRAL"
            }

        opens = df["open"].values
        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        recent = slice(-lookback, None)
        o = opens[recent]
        h = highs[recent]
        l = lows[recent]
        c = closes[recent]

        # Body percentage for each candle
        total_ranges = h - l
        bodies = np.abs(c - o)
        body_pcts = np.where(total_ranges > 0, bodies / total_ranges, 0)
        avg_body_pct = float(np.mean(body_pcts)) * 100

        # Wick analysis for last candle
        last_body = abs(closes[-1] - opens[-1])
        last_range = highs[-1] - lows[-1]
        last_upper_wick = highs[-1] - max(closes[-1], opens[-1])
        last_lower_wick = min(closes[-1], opens[-1]) - lows[-1]

        if last_range > 0:
            last_body_pct = last_body / last_range
        else:
            last_body_pct = 0

        # Classify last candle
        if closes[-1] > opens[-1] and last_body_pct > 0.7:
            last_candle_type = "STRONG_BULL"
        elif closes[-1] < opens[-1] and last_body_pct > 0.7:
            last_candle_type = "STRONG_BEAR"
        elif last_body_pct < 0.2:
            last_candle_type = "DOJI"
        elif closes[-1] > opens[-1]:
            last_candle_type = "WEAK_BULL"
        elif closes[-1] < opens[-1]:
            last_candle_type = "WEAK_BEAR"
        else:
            last_candle_type = "NEUTRAL"

        # Consecutive same-direction candles
        consecutive_bullish = 0
        consecutive_bearish = 0
        for i in range(len(c) - 1, -1, -1):
            if c[i] > o[i]:
                if consecutive_bearish > 0:
                    break
                consecutive_bullish += 1
            elif c[i] < o[i]:
                if consecutive_bullish > 0:
                    break
                consecutive_bearish += 1
            else:
                break

        # Calculate momentum score
        score = 0

        # Direction weight from consecutive candles
        score += consecutive_bullish * 12
        score -= consecutive_bearish * 12

        # Body strength of recent candles
        bullish_body_sum = sum(
            (c[i] - o[i]) / total_ranges[i]
            for i in range(len(c))
            if c[i] > o[i] and total_ranges[i] > 0
        )
        bearish_body_sum = sum(
            (o[i] - c[i]) / total_ranges[i]
            for i in range(len(c))
            if c[i] < o[i] and total_ranges[i] > 0
        )

        score += int(bullish_body_sum * 8)
        score -= int(bearish_body_sum * 8)

        # Clamp
        score = max(-100, min(100, score))

        # State
        if score > 40:
            momentum_state = "STRONG_BULLISH"
        elif score > 15:
            momentum_state = "BULLISH"
        elif score < -40:
            momentum_state = "STRONG_BEARISH"
        elif score < -15:
            momentum_state = "BEARISH"
        else:
            momentum_state = "NEUTRAL"

        return {
            "score": score,
            "consecutive_bullish": consecutive_bullish,
            "consecutive_bearish": consecutive_bearish,
            "avg_body_pct": round(avg_body_pct, 1),
            "last_candle_type": last_candle_type,
            "momentum_state": momentum_state
        }

    # ==========================================
    # V-REVERSAL DETECTION
    # ==========================================
    def detect_v_reversal(self, df, lookback=30):
        """Detect V-bottom or V-top reversal patterns.
        V-bottom: sharp drop followed by equally sharp recovery.
        V-top: sharp rally followed by equally sharp drop."""
        if df is None or len(df) < lookback:
            return {
                "pattern": "NONE",
                "strength": 0,
                "reversal_level": 0,
                "move_size": 0
            }

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        recent_h = highs[-lookback:]
        recent_l = lows[-lookback:]
        recent_c = closes[-lookback:]

        # Find the lowest low and highest high positions in the window
        min_idx = int(np.argmin(recent_l))
        max_idx = int(np.argmax(recent_h))

        min_price = float(recent_l[min_idx])
        max_price = float(recent_h[max_idx])
        current_price = float(recent_c[-1])
        total_range = max_price - min_price

        if total_range == 0:
            return {
                "pattern": "NONE",
                "strength": 0,
                "reversal_level": 0,
                "move_size": 0
            }

        # V-BOTTOM: min is in middle of window, price has recovered significantly
        if min_idx > 3 and min_idx < lookback - 3:
            # Drop before min
            pre_min_high = float(np.max(recent_h[:min_idx]))
            drop_size = pre_min_high - min_price

            # Recovery after min — use CLOSE not HIGH to avoid spike wicks triggering false V_BOTTOM
            post_min_close = float(np.max(recent_c[min_idx:]))
            recovery_size = post_min_close - min_price

            # V-bottom: recovery is at least 60% of the drop
            if drop_size > 0 and recovery_size >= drop_size * 0.6:
                # Speed check: drop and recovery should be roughly equal in bars
                bars_to_drop = min_idx
                bars_to_recover = lookback - min_idx
                speed_ratio = bars_to_recover / bars_to_drop if bars_to_drop > 0 else 999

                # Current price must still hold above 50% of the recovery (not already reversing)
                recovery_midpoint = min_price + recovery_size * 0.5
                price_still_holding = current_price >= recovery_midpoint

                if speed_ratio < 3.0 and price_still_holding:
                    strength = min(100, int((recovery_size / drop_size) * 70 + 30))
                    return {
                        "pattern": "V_BOTTOM",
                        "strength": strength,
                        "reversal_level": round(min_price, 2),
                        "move_size": round(recovery_size, 2),
                        "drop_size": round(drop_size, 2)
                    }

        # V-TOP: max is in middle of window, price has dropped significantly
        if max_idx > 3 and max_idx < lookback - 3:
            # Rally before max
            pre_max_low = float(np.min(recent_l[:max_idx]))
            rally_size = max_price - pre_max_low

            # Drop after max — use CLOSE not LOW to avoid wick-driven false V_TOP
            post_max_close = float(np.min(recent_c[max_idx:]))
            drop_size = max_price - post_max_close

            # V-top: drop is at least 60% of the rally
            if rally_size > 0 and drop_size >= rally_size * 0.6:
                bars_to_rally = max_idx
                bars_to_drop = lookback - max_idx
                speed_ratio = bars_to_drop / bars_to_rally if bars_to_rally > 0 else 999

                # Current price must still be below 50% of the drop (not already recovering)
                drop_midpoint = max_price - drop_size * 0.5
                price_still_dropping = current_price <= drop_midpoint

                if speed_ratio < 3.0 and price_still_dropping:
                    strength = min(100, int((drop_size / rally_size) * 70 + 30))
                    return {
                        "pattern": "V_TOP",
                        "strength": strength,
                        "reversal_level": round(max_price, 2),
                        "move_size": round(drop_size, 2),
                        "rally_size": round(rally_size, 2)
                    }

        return {
            "pattern": "NONE",
            "strength": 0,
            "reversal_level": 0,
            "move_size": 0
        }

    # ==========================================
    # BREAKER BLOCK DETECTION
    # ==========================================
    def detect_breaker_block(self, df, lookback=50):
        """Detect breaker blocks — failed order blocks that flip polarity.
        A bearish breaker: was a demand zone, price broke below it → now resistance.
        A bullish breaker: was a supply zone, price broke above it → now support."""
        if df is None or len(df) < lookback:
            return {"bearish_breaker": None, "bullish_breaker": None}

        highs  = df["high"].values
        lows   = df["low"].values
        opens  = df["open"].values
        closes = df["close"].values

        bearish_breaker = None
        bullish_breaker = None

        for i in range(lookback - 4, 4, -1):
            # --- BEARISH BREAKER: was bullish OB (demand), price broke below ---
            if closes[i] > opens[i]:  # bullish candle
                ob_low  = min(opens[i], closes[i])
                ob_high = max(opens[i], closes[i])
                # Check if a later candle closed BELOW this OB low
                for j in range(i + 1, min(i + 20, len(df))):
                    if closes[j] < ob_low:
                        # OB is now a breaker (resistance)
                        if bearish_breaker is None:
                            bearish_breaker = {
                                "zone_low":  round(ob_low,  2),
                                "zone_high": round(ob_high, 2),
                                "broken_at": round(closes[j], 2),
                                "bar_index": i
                            }
                        break

            # --- BULLISH BREAKER: was bearish OB (supply), price broke above ---
            if closes[i] < opens[i]:  # bearish candle
                ob_low  = min(opens[i], closes[i])
                ob_high = max(opens[i], closes[i])
                for j in range(i + 1, min(i + 20, len(df))):
                    if closes[j] > ob_high:
                        if bullish_breaker is None:
                            bullish_breaker = {
                                "zone_low":  round(ob_low,  2),
                                "zone_high": round(ob_high, 2),
                                "broken_at": round(closes[j], 2),
                                "bar_index": i
                            }
                        break

            if bearish_breaker and bullish_breaker:
                break

        return {
            "bearish_breaker": bearish_breaker,
            "bullish_breaker": bullish_breaker
        }

    # ==========================================
    # DOUBLE TOP / DOUBLE BOTTOM
    # ==========================================
    def detect_double_top_bottom(self, df, lookback=60, tolerance=0.003):
        """Detect Double Top and Double Bottom patterns.
        tolerance: how close the two peaks/troughs must be (0.3% default)."""
        if df is None or len(df) < lookback:
            return {"pattern": "NONE", "level": 0, "strength": 0}

        swing_highs, swing_lows = self.find_swings(df, lookback=5)
        highs  = df["high"].values
        lows   = df["low"].values
        closes = df["close"].values

        # --- DOUBLE TOP ---
        if len(swing_highs) >= 2:
            recent_shs = swing_highs[-min(5, len(swing_highs)):]
            for k in range(len(recent_shs) - 1, 0, -1):
                sh1_idx = recent_shs[k - 1]
                sh2_idx = recent_shs[k]
                sh1_val = highs[sh1_idx]
                sh2_val = highs[sh2_idx]
                # Two peaks within tolerance
                diff = abs(sh1_val - sh2_val) / max(sh1_val, sh2_val)
                if diff <= tolerance:
                    # Must be a valley between them
                    valley_low = min(lows[sh1_idx:sh2_idx + 1])
                    neckline   = valley_low
                    # Confirmation: current close below neckline
                    if closes[-1] < neckline:
                        strength = min(100, int((1 - diff / tolerance) * 70 + 30))
                        return {
                            "pattern":   "DOUBLE_TOP",
                            "level":     round((sh1_val + sh2_val) / 2, 2),
                            "neckline":  round(neckline, 2),
                            "strength":  strength
                        }

        # --- DOUBLE BOTTOM ---
        if len(swing_lows) >= 2:
            recent_sls = swing_lows[-min(5, len(swing_lows)):]
            for k in range(len(recent_sls) - 1, 0, -1):
                sl1_idx = recent_sls[k - 1]
                sl2_idx = recent_sls[k]
                sl1_val = lows[sl1_idx]
                sl2_val = lows[sl2_idx]
                diff = abs(sl1_val - sl2_val) / max(sl1_val, sl2_val)
                if diff <= tolerance:
                    peak_high = max(highs[sl1_idx:sl2_idx + 1])
                    neckline  = peak_high
                    if closes[-1] > neckline:
                        strength = min(100, int((1 - diff / tolerance) * 70 + 30))
                        return {
                            "pattern":  "DOUBLE_BOTTOM",
                            "level":    round((sl1_val + sl2_val) / 2, 2),
                            "neckline": round(neckline, 2),
                            "strength": strength
                        }

        return {"pattern": "NONE", "level": 0, "strength": 0}

    # ==========================================
    # INSIDE BAR (Compression → Breakout)
    # ==========================================
    def detect_inside_bar(self, df, lookback=5):
        """Detect inside bar compression setup.
        Inside bar: current candle's high/low is fully within previous candle's range.
        Multiple consecutive inside bars = strong compression before breakout."""
        if df is None or len(df) < 4:
            return {"detected": False, "count": 0, "bias": "NONE", "mother_high": 0, "mother_low": 0}

        highs  = df["high"].values
        lows   = df["low"].values
        closes = df["close"].values

        # Count consecutive inside bars going back
        count = 0
        mother_idx = len(df) - 2  # default mother bar
        for i in range(len(df) - 1, 0, -1):
            if highs[i] < highs[i - 1] and lows[i] > lows[i - 1]:
                count += 1
                mother_idx = i - 1
            else:
                break

        if count == 0:
            return {"detected": False, "count": 0, "bias": "NONE", "mother_high": 0, "mother_low": 0}

        mother_high = highs[mother_idx]
        mother_low  = lows[mother_idx]
        mother_body = closes[mother_idx] - df["open"].values[mother_idx]

        # Bias from mother candle direction
        bias = "BULLISH" if mother_body > 0 else "BEARISH"

        return {
            "detected":    True,
            "count":       count,
            "bias":        bias,
            "mother_high": round(mother_high, 2),
            "mother_low":  round(mother_low,  2),
            "breakout_up": round(mother_high, 2),
            "breakout_dn": round(mother_low,  2)
        }

    # ==========================================
    # MORNING STAR / EVENING STAR
    # ==========================================
    def detect_morning_evening_star(self, df):
        """Detect 3-candle Morning Star (bullish reversal) and Evening Star (bearish reversal).
        Morning Star: big bearish → small body (doji/spinner) → big bullish
        Evening Star: big bullish → small body → big bearish"""
        if df is None or len(df) < 5:
            return {"pattern": "NONE", "strength": 0}

        o = df["open"].values
        h = df["high"].values
        l = df["low"].values
        c = df["close"].values

        # Last 3 candles: -3, -2, -1
        c1_o, c1_c = o[-3], c[-3]
        c2_o, c2_c = o[-2], c[-2]
        c3_o, c3_c = o[-1], c[-1]

        c1_range = abs(h[-3] - l[-3])
        c2_range = abs(h[-2] - l[-2])
        c3_range = abs(h[-1] - l[-1])

        if c1_range == 0 or c3_range == 0:
            return {"pattern": "NONE", "strength": 0}

        c1_body = abs(c1_c - c1_o) / c1_range
        c2_body = abs(c2_c - c2_o) / (c2_range if c2_range > 0 else 1)
        c3_body = abs(c3_c - c3_o) / c3_range

        # --- MORNING STAR (bullish reversal) ---
        if (c1_c < c1_o and           # candle 1 bearish
            c1_body > 0.6 and         # strong body
            c2_body < 0.3 and         # candle 2 small (doji/spinner)
            c3_c > c3_o and           # candle 3 bullish
            c3_body > 0.5 and         # strong body
            c3_c > (c1_o + c1_c) / 2  # closes above midpoint of candle 1
        ):
            strength = min(100, int((c1_body + c3_body) / 2 * 80 + 20))
            return {
                "pattern":  "MORNING_STAR",
                "strength": strength,
                "level":    round(min(l[-3], l[-2], l[-1]), 2)
            }

        # --- EVENING STAR (bearish reversal) ---
        if (c1_c > c1_o and           # candle 1 bullish
            c1_body > 0.6 and
            c2_body < 0.3 and         # candle 2 small
            c3_c < c3_o and           # candle 3 bearish
            c3_body > 0.5 and
            c3_c < (c1_o + c1_c) / 2  # closes below midpoint of candle 1
        ):
            strength = min(100, int((c1_body + c3_body) / 2 * 80 + 20))
            return {
                "pattern":  "EVENING_STAR",
                "strength": strength,
                "level":    round(max(h[-3], h[-2], h[-1]), 2)
            }

        return {"pattern": "NONE", "strength": 0}

    # ==========================================
    # WYCKOFF SPRING / UPTHRUST
    # ==========================================
    def detect_wyckoff_spring_upthrust(self, df, lookback=40):
        """Detect Wyckoff Spring (bullish) and Upthrust (bearish).
        Spring: price briefly dips below a key support (range low) then quickly recovers.
        Upthrust: price briefly pops above a key resistance (range high) then quickly reverses.
        These are the same as liquidity sweeps but validated by Wyckoff context (prior range)."""
        if df is None or len(df) < lookback:
            return {"pattern": "NONE", "level": 0, "strength": 0}

        highs  = df["high"].values
        lows   = df["low"].values
        closes = df["close"].values

        # Define the trading range (excluding last 5 candles)
        range_window = lows[-lookback:-5]
        range_highs  = highs[-lookback:-5]

        range_low  = float(np.min(range_window))
        range_high = float(np.max(range_highs))
        range_size = range_high - range_low

        if range_size <= 0:
            return {"pattern": "NONE", "level": 0, "strength": 0}

        current_close = closes[-1]
        recent_low    = float(np.min(lows[-5:]))
        recent_high   = float(np.max(highs[-5:]))

        # --- SPRING: dipped below range_low then recovered above it ---
        if recent_low < range_low and current_close > range_low:
            penetration = (range_low - recent_low) / range_size * 100
            if penetration < 15:  # shallow false break = spring
                strength = min(100, int(80 - penetration * 2))
                return {
                    "pattern":     "WYCKOFF_SPRING",
                    "level":       round(range_low, 2),
                    "penetration": round(penetration, 1),
                    "strength":    strength
                }

        # --- UPTHRUST: popped above range_high then reversed back below ---
        if recent_high > range_high and current_close < range_high:
            penetration = (recent_high - range_high) / range_size * 100
            if penetration < 15:
                strength = min(100, int(80 - penetration * 2))
                return {
                    "pattern":     "WYCKOFF_UPTHRUST",
                    "level":       round(range_high, 2),
                    "penetration": round(penetration, 1),
                    "strength":    strength
                }

        return {"pattern": "NONE", "level": 0, "strength": 0}

    # ==========================================
    # DAILY ZONE DETECTION
    # ==========================================
    def find_daily_supply_zone(self, df_1d, lookback=20):
        """Find supply zone on Daily timeframe — strongest level"""
        if df_1d is None or len(df_1d) < 10:
            return None
        return self.find_supply_zone(df_1d, lookback=lookback)

    def find_daily_demand_zone(self, df_1d, lookback=20):
        """Find demand zone on Daily timeframe — strongest level"""
        if df_1d is None or len(df_1d) < 10:
            return None
        return self.find_demand_zone(df_1d, lookback=lookback)

    # ==========================================
    # KEY LEVELS (Day High/Low, Previous Day H/L)
    # ==========================================
    def get_key_levels(self, df_1h):
        """Get key institutional levels from 1H data"""
        if df_1h is None or len(df_1h) < 24:
            return {}

        # Last 24 candles = ~1 day on 1H
        day_data = df_1h.tail(24)
        prev_day = df_1h.iloc[-48:-24] if len(df_1h) >= 48 else df_1h.head(24)

        day_high = day_data["high"].max()
        day_low = day_data["low"].min()
        prev_day_high = prev_day["high"].max()
        prev_day_low = prev_day["low"].min()

        # Asian session range (first 5 candles of day = 00:00-05:00 UTC)
        asian_range_high = day_data.head(5)["high"].max()
        asian_range_low = day_data.head(5)["low"].min()

        return {
            "day_high": day_high,
            "day_low": day_low,
            "prev_day_high": prev_day_high,
            "prev_day_low": prev_day_low,
            "asian_high": asian_range_high,
            "asian_low": asian_range_low,
            "mid_point": (day_high + day_low) / 2
        }

    # ==========================================
    # PREDICTIVE SETUP GENERATOR
    # ==========================================
    def generate_predictive_setup(self, df_1h, df_15m, df_5m, df_1d=None):
        """Generate conditional trade setup for next 1HR move
        
        This is the core function that creates PREDICTIVE setups:
        - Analyzes structure across timeframes
        - Identifies key levels and zones
        - Creates IF-THEN conditional entries
        - Provides SL/TP based on structure, not fixed ATR
        - NEW: Channel detection, candle momentum, V-reversal, Daily zones
        """
        if df_1h is None or df_15m is None or df_5m is None:
            return self._no_setup("Missing timeframe data")

        if len(df_5m) < 30 or len(df_15m) < 30 or len(df_1h) < 24:
            return self._no_setup("Insufficient data")

        current_price = float(df_5m["close"].iloc[-1])

        # Step 1: HTF Trend (1H)
        trend_1h, structure_1h = self.detect_market_structure(df_1h)

        # Step 2: Key Levels
        key_levels = self.get_key_levels(df_1h)

        # Step 3: Supply/Demand Zones (15m)
        supply_zone = self.find_supply_zone(df_15m)
        demand_zone = self.find_demand_zone(df_15m)

        # Step 4: Swing structure (5m)
        swing_highs_5m, swing_lows_5m = self.find_swings(df_5m, lookback=3)

        # Step 5: Liquidity sweeps (5m)
        buy_sweep, buy_sweep_level = self.detect_liquidity_sweep_buy_side(df_5m)
        sell_sweep, sell_sweep_level = self.detect_liquidity_sweep_sell_side(df_5m)

        # Step 6: BOS/CHOCH (5m)
        bos_bullish, bos_bull_level = self.detect_bos_bullish(df_5m)
        bos_bearish, bos_bear_level = self.detect_bos_bearish(df_5m)
        choch_bullish, choch_bull_level = self.detect_choch_bullish(df_5m)
        choch_bearish, choch_bear_level = self.detect_choch_bearish(df_5m)

        # Step 7: Confirmation candles (5m)
        bear_confirm = self.detect_bearish_confirmation(df_5m)
        bull_confirm = self.detect_bullish_confirmation(df_5m)

        # Step 8: NEW — Channel Detection (1H)
        channel_1h = self.detect_channel(df_1h)

        # Step 9: NEW — Candle Momentum (1H for trend, 5m for entry)
        momentum_1h = self.candle_momentum_score(df_1h, lookback=10)
        momentum_5m = self.candle_momentum_score(df_5m, lookback=10)

        # Step 10: NEW — V-Reversal Detection (1H)
        v_reversal = self.detect_v_reversal(df_1h, lookback=24)

        # Step 11: NEW — Daily Supply/Demand Zones
        daily_supply = self.find_daily_supply_zone(df_1d) if df_1d is not None else None
        daily_demand = self.find_daily_demand_zone(df_1d) if df_1d is not None else None

        # Step 12: NEW — Breaker Block (15m)
        breaker = self.detect_breaker_block(df_15m)

        # Step 13: NEW — Double Top / Double Bottom (1H)
        double_pattern = self.detect_double_top_bottom(df_1h)

        # Step 14: NEW — Inside Bar compression (5m)
        inside_bar = self.detect_inside_bar(df_5m)

        # Step 15: NEW — Morning / Evening Star (5m)
        star_pattern = self.detect_morning_evening_star(df_5m)

        # Step 16: NEW — Wyckoff Spring / Upthrust (1H)
        wyckoff = self.detect_wyckoff_spring_upthrust(df_1h)

        # ==================================
        # PREDICTIVE SETUP — PURE PRICE ACTION
        # ==================================
        # RULE: 1H structure LOCKS the direction. Score only measures
        # how many LTF entry conditions are confirmed (zone, sweep,
        # confirm candle, BOS/CHOCH). Direction NEVER flips due to score.
        # ==================================

        # --- STEP A: DIRECTION FROM 1H STRUCTURE (immutable) ---
        if trend_1h == "BEARISH":
            pa_direction = "SELL"
        elif trend_1h == "BULLISH":
            pa_direction = "BUY"
        else:
            # NEUTRAL 1H: use momentum as tiebreaker, still observe both
            if momentum_1h["momentum_state"] in ["STRONG_BEARISH", "BEARISH"]:
                pa_direction = "SELL"
            elif momentum_1h["momentum_state"] in ["STRONG_BULLISH", "BULLISH"]:
                pa_direction = "BUY"
            else:
                pa_direction = "NEUTRAL"

        # --- STEP B: OBSERVATION — what price action shows (both sides) ---
        obs_met = []
        obs_pending = []

        # 1H structure context
        obs_met.append(f"1H structure: {trend_1h} ({structure_1h})")

        # Momentum context (observation only, not direction)
        mom_state = momentum_1h["momentum_state"]
        if mom_state != "NEUTRAL":
            obs_met.append(f"1H momentum: {mom_state} ({momentum_1h['score']})")

        # V-reversal (observation only)
        if v_reversal["pattern"] != "NONE" and v_reversal["strength"] >= 60:
            obs_met.append(f"V-Reversal: {v_reversal['pattern']} at ${v_reversal['reversal_level']:.2f} ({v_reversal['strength']}%)")

        # Channel position
        if channel_1h["type"] != "NONE":
            obs_met.append(f"Channel: {channel_1h['type']} | Position: {channel_1h['position']:.0%}")

        # Double Top / Bottom (1H)
        if double_pattern["pattern"] != "NONE":
            obs_met.append(f"{double_pattern['pattern']} at ${double_pattern['level']:,.2f} | Neckline: ${double_pattern.get('neckline',0):,.2f} ({double_pattern['strength']}%)")

        # Wyckoff Spring / Upthrust (1H)
        if wyckoff["pattern"] != "NONE":
            obs_met.append(f"{wyckoff['pattern']} at ${wyckoff['level']:,.2f} | Penetration: {wyckoff.get('penetration',0)}% ({wyckoff['strength']}%)")

        # Inside Bar compression (5m)
        if inside_bar["detected"]:
            obs_met.append(f"Inside Bar x{inside_bar['count']} ({inside_bar['bias']}) | Break above ${inside_bar['breakout_up']:,.2f} or below ${inside_bar['breakout_dn']:,.2f}")

        # Morning / Evening Star (5m)
        if star_pattern["pattern"] != "NONE":
            obs_met.append(f"{star_pattern['pattern']} at ${star_pattern['level']:,.2f} ({star_pattern['strength']}%)")

        # Breaker Blocks (15m)
        if breaker["bearish_breaker"]:
            bb = breaker["bearish_breaker"]
            obs_met.append(f"Bearish Breaker Block ${bb['zone_low']:,.2f}-${bb['zone_high']:,.2f} (broke at ${bb['broken_at']:,.2f})")
        if breaker["bullish_breaker"]:
            bb = breaker["bullish_breaker"]
            obs_met.append(f"Bullish Breaker Block ${bb['zone_low']:,.2f}-${bb['zone_high']:,.2f} (broke at ${bb['broken_at']:,.2f})")

        # Daily zones
        if daily_supply:
            ds_low, ds_high, ds_str = daily_supply
            if ds_low <= current_price <= ds_high:
                obs_met.append(f"IN Daily supply ${ds_low:.2f}-${ds_high:.2f}")
            else:
                obs_met.append(f"Daily supply: ${ds_low:.2f}-${ds_high:.2f}")
        if daily_demand:
            dd_low, dd_high, dd_str = daily_demand
            if dd_low <= current_price <= dd_high:
                obs_met.append(f"IN Daily demand ${dd_low:.2f}-${dd_high:.2f}")
            else:
                obs_met.append(f"Daily demand: ${dd_low:.2f}-${dd_high:.2f}")

        # --- STEP C: ENTRY READINESS SCORE (LTF conditions only) ---
        # This score measures how many entry triggers have fired.
        # It does NOT determine direction — direction is already locked above.
        entry_score = 0
        entry_conditions_met = []
        entry_conditions_pending = []

        if pa_direction == "SELL":
            # Zone
            if supply_zone:
                sz_low, sz_high, sz_str = supply_zone
                if sz_low <= current_price <= sz_high:
                    entry_score += 30
                    entry_conditions_met.append(f"Price IN supply zone ${sz_low:.2f}-${sz_high:.2f}")
                elif sz_low > current_price:
                    dist = sz_low - current_price
                    entry_conditions_pending.append(f"Wait for price to reach supply ${sz_low:.2f}-${sz_high:.2f} (${dist:.0f} away)")
                else:
                    entry_conditions_pending.append(f"Supply zone ${sz_low:.2f}-${sz_high:.2f} below price — wait for new zone")
            else:
                entry_conditions_pending.append("No supply zone detected on 15m")
            # Liquidity sweep
            if buy_sweep:
                entry_score += 25
                entry_conditions_met.append(f"Buy-side liquidity swept at ${buy_sweep_level:.2f}")
            else:
                entry_conditions_pending.append("Wait for buy-side liquidity sweep")
            # Bearish confirmation candle
            if bear_confirm:
                entry_score += 25
                entry_conditions_met.append(f"Bearish confirmation candle: {bear_confirm}")
            else:
                entry_conditions_pending.append("Wait for bearish confirmation candle")
            # BOS/CHOCH
            if bos_bearish:
                entry_score += 20
                entry_conditions_met.append(f"Bearish BOS confirmed at ${bos_bear_level:.2f}")
            elif choch_bearish:
                entry_score += 20
                entry_conditions_met.append(f"Bearish CHOCH confirmed at ${choch_bear_level:.2f}")
            else:
                entry_conditions_pending.append("Wait for bearish BOS/CHOCH on 5m")
            # SL/TP from structure
            # Entry = top of supply zone (where price arrives for SELL)
            sell_entry = supply_zone[0] if supply_zone else current_price
            sell_sl = 0
            sell_tp = 0
            if supply_zone:
                sell_sl = supply_zone[1] + (supply_zone[1] - supply_zone[0]) * 0.5
            elif channel_1h["type"] != "NONE" and channel_1h["upper"] > 0:
                sell_sl = channel_1h["upper"] + channel_1h["width"] * 0.1
            elif key_levels.get("day_high"):
                sell_sl = key_levels["day_high"] + 50
            if demand_zone:
                sell_tp = demand_zone[0]
            elif channel_1h["type"] != "NONE" and channel_1h["lower"] > 0:
                sell_tp = channel_1h["lower"]
            elif key_levels.get("day_low"):
                sell_tp = key_levels["day_low"]
            elif swing_lows_5m and len(swing_lows_5m) >= 2:
                sell_tp = df_5m["low"].values[swing_lows_5m[-2]]
            final_entry = sell_entry
            final_sl = round(sell_sl, 2)
            final_tp = round(sell_tp, 2)

        elif pa_direction == "BUY":
            # Zone
            if demand_zone:
                dz_low, dz_high, dz_str = demand_zone
                if dz_low <= current_price <= dz_high:
                    entry_score += 30
                    entry_conditions_met.append(f"Price IN demand zone ${dz_low:.2f}-${dz_high:.2f}")
                elif current_price > dz_high:
                    dist = current_price - dz_high
                    entry_conditions_pending.append(f"Price approaching demand ${dz_low:.2f}-${dz_high:.2f} (${dist:.0f} away)")
                else:
                    entry_conditions_pending.append(f"Demand zone ${dz_low:.2f}-${dz_high:.2f} above price — wait for new zone")
            else:
                entry_conditions_pending.append("No demand zone detected on 15m")
            # Liquidity sweep
            if sell_sweep:
                entry_score += 25
                entry_conditions_met.append(f"Sell-side liquidity swept at ${sell_sweep_level:.2f}")
            else:
                entry_conditions_pending.append("Wait for sell-side liquidity sweep")
            # Bullish confirmation candle
            if bull_confirm:
                entry_score += 25
                entry_conditions_met.append(f"Bullish confirmation candle: {bull_confirm}")
            else:
                entry_conditions_pending.append("Wait for bullish confirmation candle")
            # BOS/CHOCH
            if bos_bullish:
                entry_score += 20
                entry_conditions_met.append(f"Bullish BOS confirmed at ${bos_bull_level:.2f}")
            elif choch_bullish:
                entry_score += 20
                entry_conditions_met.append(f"Bullish CHOCH confirmed at ${choch_bull_level:.2f}")
            else:
                entry_conditions_pending.append("Wait for bullish BOS/CHOCH on 5m")
            # SL/TP from structure
            # Entry = bottom of demand zone (where price arrives for BUY)
            buy_entry = demand_zone[1] if demand_zone else current_price
            buy_sl = 0
            buy_tp = 0
            if demand_zone:
                buy_sl = demand_zone[0] - (demand_zone[1] - demand_zone[0]) * 0.5
            elif channel_1h["type"] != "NONE" and channel_1h["lower"] > 0:
                buy_sl = channel_1h["lower"] - channel_1h["width"] * 0.1
            elif key_levels.get("day_low"):
                buy_sl = key_levels["day_low"] - 50
            if supply_zone:
                buy_tp = supply_zone[1]
            elif channel_1h["type"] != "NONE" and channel_1h["upper"] > 0:
                buy_tp = channel_1h["upper"]
            elif key_levels.get("day_high"):
                buy_tp = key_levels["day_high"]
            elif swing_highs_5m and len(swing_highs_5m) >= 2:
                buy_tp = df_5m["high"].values[swing_highs_5m[-2]]
            final_entry = buy_entry
            final_sl = round(buy_sl, 2)
            final_tp = round(buy_tp, 2)

        else:
            # NEUTRAL — no entry, just observe
            entry_conditions_pending.append("1H structure NEUTRAL — wait for clear HH/HL or LH/LL")
            final_entry = current_price
            final_sl = 0
            final_tp = 0

        # Entry is ready when 3 of 4 LTF conditions are met (score >= 75)
        entry_ready = (entry_score >= 75 and len(entry_conditions_pending) <= 1)
        final_rr = abs(final_entry - final_tp) / abs(final_sl - final_entry) if final_sl > 0 and final_sl != final_entry else 0

        # Combined conditions for display
        all_conditions_met = obs_met + entry_conditions_met
        all_conditions_pending = entry_conditions_pending

        # Build single best setup from HTF-locked direction
        best = {
            "direction": pa_direction,
            "score": entry_score,
            "entry": final_entry,
            "sl": final_sl,
            "tp": final_tp,
            "rr": round(final_rr, 2),
            "conditions_met": all_conditions_met,
            "conditions_pending": all_conditions_pending,
            "ready": entry_ready
        }
        setups = [best]
        return {
            "signal": best["direction"] if best["ready"] else "WATCH_" + best["direction"],
            "setup_ready": best["ready"],
            "entry": round(best["entry"], 2),
            "sl": best["sl"],
            "tp": best["tp"],
            "rr": best["rr"],
            "score": best["score"],
            "conditions_met": best["conditions_met"],
            "conditions_pending": best["conditions_pending"],
            "trend": trend_1h,
            "structure": structure_1h,
            "supply_zone": (supply_zone[0], supply_zone[1]) if supply_zone else None,
            "demand_zone": (demand_zone[0], demand_zone[1]) if demand_zone else None,
            "key_levels": key_levels,
            "all_setups": setups,
            "channel": channel_1h,
            "momentum_1h": momentum_1h,
            "momentum_5m": momentum_5m,
            "v_reversal": v_reversal,
            "daily_supply": (daily_supply[0], daily_supply[1]) if daily_supply else None,
            "daily_demand": (daily_demand[0], daily_demand[1]) if daily_demand else None,
            "breaker": breaker,
            "double_pattern": double_pattern,
            "inside_bar": inside_bar,
            "star_pattern": star_pattern,
            "wyckoff": wyckoff,
            "reason": "Setup generated from multi-timeframe analysis"
        }

    # ==========================================
    # GENERATE INSTITUTIONAL ENTRY
    # (called by get_trade_setup.py)
    # ==========================================
    def generate_institutional_entry(self, df_1h, df_15m, df_5m):
        """Generate institutional entry — wrapper for get_trade_setup.py compatibility"""
        setup = self.generate_predictive_setup(df_1h, df_15m, df_5m)

        if setup["signal"] == "NO TRADE":
            return {
                "signal": "NO TRADE",
                "reason": setup.get("reason", "No setup")
            }

        # Only return executable signal if setup is fully ready
        if setup["setup_ready"]:
            return {
                "signal": setup["signal"].replace("WATCH_", ""),
                "entry": setup["entry"],
                "sl": setup["sl"],
                "tp": setup["tp"],
                "confidence": setup["score"],
                "trend": setup["trend"],
                "structure": setup["structure"],
                "supply_zone": setup.get("supply_zone"),
                "demand_zone": setup.get("demand_zone"),
                "liquidity_sweep": setup.get("entry", 0),
                "confirmation": ", ".join(setup["conditions_met"][-2:]),
                "bos": any("BOS" in c for c in setup["conditions_met"]),
                "reason": "All conditions met"
            }
        else:
            return {
                "signal": "NO TRADE",
                "reason": f"Setup forming ({setup['score']}%) — Pending: {'; '.join(setup['conditions_pending'][:2])}"
            }

    # ==========================================
    # HELPER
    # ==========================================
    def _no_setup(self, reason):
        return {
            "signal": "NO TRADE",
            "setup_ready": False,
            "entry": 0,
            "sl": 0,
            "tp": 0,
            "rr": 0,
            "score": 0,
            "conditions_met": [],
            "conditions_pending": [reason],
            "trend": "NEUTRAL",
            "structure": "UNKNOWN",
            "supply_zone": None,
            "demand_zone": None,
            "key_levels": {},
            "all_setups": [],
            "reason": reason
        }
