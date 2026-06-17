# ==========================================
# IPA LOGGER
# Logs every scan and every trade
# Two files:
#   ipa_scan_log.csv  — every 60s analysis snapshot
#   ipa_trade_log.csv — every trade entry + exit
# ==========================================

import os
import csv
from datetime import datetime


class IPALogger:

    SCAN_FILE  = "ipa_scan_log.csv"
    TRADE_FILE = "ipa_trade_log.csv"

    SCAN_COLS = [
        "timestamp", "symbol", "price",
        # Direction & readiness
        "signal", "direction", "entry_score", "setup_ready",
        # Trade levels
        "entry", "sl", "tp", "rr",
        # 1H structure
        "trend_1h", "structure_1h",
        # Momentum
        "momentum_1h_state", "momentum_1h_score",
        "momentum_5m_state", "momentum_5m_score",
        # Zones
        "supply_zone_low", "supply_zone_high",
        "demand_zone_low", "demand_zone_high",
        "daily_supply_low", "daily_supply_high",
        "daily_demand_low", "daily_demand_high",
        # Patterns
        "v_reversal_pattern", "v_reversal_strength", "v_reversal_level",
        "channel_type", "channel_position", "channel_strength",
        "double_pattern", "double_level", "double_neckline", "double_strength",
        "inside_bar_detected", "inside_bar_count", "inside_bar_bias",
        "star_pattern", "star_strength",
        "wyckoff_pattern", "wyckoff_level", "wyckoff_strength",
        "bearish_breaker_low", "bearish_breaker_high",
        "bullish_breaker_low", "bullish_breaker_high",
        # LTF confirmations
        "buy_sweep", "sell_sweep",
        "bull_confirm", "bear_confirm",
        "bos_bullish", "bos_bearish",
        "choch_bullish", "choch_bearish",
        # All confirmed conditions (joined)
        "conditions_met",
        "conditions_pending",
        # Session
        "session",
    ]

    TRADE_COLS = [
        "timestamp", "symbol",
        # Entry details
        "direction", "entry_price", "sl", "tp", "rr", "entry_score",
        # Setup at entry
        "trend_1h", "structure_1h",
        "momentum_1h_state", "momentum_1h_score",
        "v_reversal_pattern", "v_reversal_strength",
        "double_pattern", "double_strength",
        "star_pattern", "star_strength",
        "wyckoff_pattern", "wyckoff_strength",
        "inside_bar_detected", "inside_bar_count",
        "channel_type", "channel_position",
        "supply_zone", "demand_zone",
        "daily_supply", "daily_demand",
        "bearish_breaker", "bullish_breaker",
        "conditions_met",
        # Exit details
        "exit_price", "exit_time", "result",
        "pnl_points", "pnl_pct", "duration_min",
        "max_pnl", "min_pnl",
    ]

    def __init__(self):
        self._ensure_file(self.SCAN_FILE,  self.SCAN_COLS)
        self._ensure_file(self.TRADE_FILE, self.TRADE_COLS)

    def _ensure_file(self, filename, cols):
        if not os.path.exists(filename):
            with open(filename, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=cols).writeheader()
            print(f"[LOGGER] Created {filename}")

    def _append(self, filename, cols, row: dict):
        with open(filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            writer.writerow(row)

    # ==========================================
    # LOG SCAN (called every 60s per symbol)
    # ==========================================
    def log_scan(self, symbol, setup: dict, session: str = ""):
        if setup is None:
            return

        m1h = setup.get("momentum_1h", {})
        m5m = setup.get("momentum_5m", {})
        v   = setup.get("v_reversal", {})
        ch  = setup.get("channel", {})
        dp  = setup.get("double_pattern", {})
        ib  = setup.get("inside_bar", {})
        sp  = setup.get("star_pattern", {})
        wk  = setup.get("wyckoff", {})
        bk  = setup.get("breaker", {})
        sz  = setup.get("supply_zone")
        dz  = setup.get("demand_zone")
        ds  = setup.get("daily_supply")
        dd  = setup.get("daily_demand")

        bb_bear = bk.get("bearish_breaker") if bk else None
        bb_bull = bk.get("bullish_breaker") if bk else None

        row = {
            "timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol":             symbol,
            "price":              setup.get("entry", 0),
            "signal":             setup.get("signal", ""),
            "direction":          setup.get("trend", ""),
            "entry_score":        setup.get("score", 0),
            "setup_ready":        setup.get("setup_ready", False),
            "entry":              setup.get("entry", 0),
            "sl":                 setup.get("sl", 0),
            "tp":                 setup.get("tp", 0),
            "rr":                 setup.get("rr", 0),
            "trend_1h":           setup.get("trend", ""),
            "structure_1h":       setup.get("structure", ""),
            "momentum_1h_state":  m1h.get("momentum_state", ""),
            "momentum_1h_score":  m1h.get("score", 0),
            "momentum_5m_state":  m5m.get("momentum_state", ""),
            "momentum_5m_score":  m5m.get("score", 0),
            "supply_zone_low":    sz[0] if sz else "",
            "supply_zone_high":   sz[1] if sz else "",
            "demand_zone_low":    dz[0] if dz else "",
            "demand_zone_high":   dz[1] if dz else "",
            "daily_supply_low":   ds[0] if ds else "",
            "daily_supply_high":  ds[1] if ds else "",
            "daily_demand_low":   dd[0] if dd else "",
            "daily_demand_high":  dd[1] if dd else "",
            "v_reversal_pattern": v.get("pattern", "NONE"),
            "v_reversal_strength":v.get("strength", 0),
            "v_reversal_level":   v.get("reversal_level", 0),
            "channel_type":       ch.get("type", "NONE"),
            "channel_position":   ch.get("position", 0),
            "channel_strength":   ch.get("strength", 0),
            "double_pattern":     dp.get("pattern", "NONE"),
            "double_level":       dp.get("level", 0),
            "double_neckline":    dp.get("neckline", 0),
            "double_strength":    dp.get("strength", 0),
            "inside_bar_detected":ib.get("detected", False),
            "inside_bar_count":   ib.get("count", 0),
            "inside_bar_bias":    ib.get("bias", "NONE"),
            "star_pattern":       sp.get("pattern", "NONE"),
            "star_strength":      sp.get("strength", 0),
            "wyckoff_pattern":    wk.get("pattern", "NONE"),
            "wyckoff_level":      wk.get("level", 0),
            "wyckoff_strength":   wk.get("strength", 0),
            "bearish_breaker_low":  bb_bear["zone_low"]  if bb_bear else "",
            "bearish_breaker_high": bb_bear["zone_high"] if bb_bear else "",
            "bullish_breaker_low":  bb_bull["zone_low"]  if bb_bull else "",
            "bullish_breaker_high": bb_bull["zone_high"] if bb_bull else "",
            "buy_sweep":          "",
            "sell_sweep":         "",
            "bull_confirm":       "",
            "bear_confirm":       "",
            "bos_bullish":        "",
            "bos_bearish":        "",
            "choch_bullish":      "",
            "choch_bearish":      "",
            "conditions_met":     " | ".join(setup.get("conditions_met", [])),
            "conditions_pending": " | ".join(setup.get("conditions_pending", [])),
            "session":            session,
        }

        self._append(self.SCAN_FILE, self.SCAN_COLS, row)

    # ==========================================
    # LOG TRADE ENTRY
    # ==========================================
    def log_trade_entry(self, symbol, trade: dict, setup: dict):
        if trade is None or setup is None:
            return

        m1h = setup.get("momentum_1h", {})
        v   = setup.get("v_reversal", {})
        ch  = setup.get("channel", {})
        dp  = setup.get("double_pattern", {})
        ib  = setup.get("inside_bar", {})
        sp  = setup.get("star_pattern", {})
        wk  = setup.get("wyckoff", {})
        bk  = setup.get("breaker", {})
        sz  = setup.get("supply_zone")
        dz  = setup.get("demand_zone")
        ds  = setup.get("daily_supply")
        dd  = setup.get("daily_demand")
        bb_bear = bk.get("bearish_breaker") if bk else None
        bb_bull = bk.get("bullish_breaker") if bk else None

        row = {
            "timestamp":          trade["entry_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "symbol":             symbol,
            "direction":          trade["direction"],
            "entry_price":        trade["entry"],
            "sl":                 trade["sl"],
            "tp":                 trade["tp"],
            "rr":                 trade.get("rr", 0),
            "entry_score":        trade.get("score", 0),
            "trend_1h":           setup.get("trend", ""),
            "structure_1h":       setup.get("structure", ""),
            "momentum_1h_state":  m1h.get("momentum_state", ""),
            "momentum_1h_score":  m1h.get("score", 0),
            "v_reversal_pattern": v.get("pattern", "NONE"),
            "v_reversal_strength":v.get("strength", 0),
            "double_pattern":     dp.get("pattern", "NONE"),
            "double_strength":    dp.get("strength", 0),
            "star_pattern":       sp.get("pattern", "NONE"),
            "star_strength":      sp.get("strength", 0),
            "wyckoff_pattern":    wk.get("pattern", "NONE"),
            "wyckoff_strength":   wk.get("strength", 0),
            "inside_bar_detected":ib.get("detected", False),
            "inside_bar_count":   ib.get("count", 0),
            "channel_type":       ch.get("type", "NONE"),
            "channel_position":   ch.get("position", 0),
            "supply_zone":        f"{sz[0]}-{sz[1]}" if sz else "",
            "demand_zone":        f"{dz[0]}-{dz[1]}" if dz else "",
            "daily_supply":       f"{ds[0]}-{ds[1]}" if ds else "",
            "daily_demand":       f"{dd[0]}-{dd[1]}" if dd else "",
            "bearish_breaker":    f"{bb_bear['zone_low']}-{bb_bear['zone_high']}" if bb_bear else "",
            "bullish_breaker":    f"{bb_bull['zone_low']}-{bb_bull['zone_high']}" if bb_bull else "",
            "conditions_met":     " | ".join(setup.get("conditions_met", [])),
            # Exit filled later
            "exit_price": "", "exit_time": "", "result": "",
            "pnl_points": "", "pnl_pct": "", "duration_min": "",
            "max_pnl": "", "min_pnl": "",
        }

        self._append(self.TRADE_FILE, self.TRADE_COLS, row)
        print(f"[LOGGER] Trade entry logged: {symbol} {trade['direction']} @ {trade['entry']}")

    # ==========================================
    # LOG TRADE EXIT (update last row for symbol)
    # ==========================================
    def log_trade_exit(self, symbol, trade: dict):
        if trade is None:
            return

        import pandas as pd
        if not os.path.exists(self.TRADE_FILE):
            return

        df = pd.read_csv(self.TRADE_FILE, encoding="utf-8")
        # Find last open trade for this symbol (no exit_price yet)
        mask = (df["symbol"] == symbol) & (df["exit_price"].astype(str).str.strip() == "")
        if not mask.any():
            return

        idx = df[mask].index[-1]
        entry_time = datetime.strptime(str(df.at[idx, "timestamp"]), "%Y-%m-%d %H:%M:%S")
        exit_time  = trade.get("exit_time", datetime.now())
        duration   = int((exit_time - entry_time).total_seconds() // 60)

        df.at[idx, "exit_price"]   = trade.get("exit_price", "")
        df.at[idx, "exit_time"]    = exit_time.strftime("%Y-%m-%d %H:%M:%S")
        df.at[idx, "result"]       = trade.get("result", "")
        df.at[idx, "pnl_points"]   = round(trade.get("final_pnl", 0), 4)
        df.at[idx, "pnl_pct"]      = round(trade.get("final_pnl_pct", 0), 4)
        df.at[idx, "duration_min"] = duration
        df.at[idx, "max_pnl"]      = round(trade.get("max_pnl", 0), 4)
        df.at[idx, "min_pnl"]      = round(trade.get("min_pnl", 0), 4)

        df.to_csv(self.TRADE_FILE, index=False, encoding="utf-8")
        print(f"[LOGGER] Trade exit logged: {symbol} {trade.get('result','')} @ {trade.get('exit_price','')}")
