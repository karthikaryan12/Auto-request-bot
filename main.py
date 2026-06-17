# ==========================================
# BTC + GOLD PRICE ACTION BOT
# Pure IPA — parallel analysis
# Direction locked by 1H structure
# ==========================================

import sys
import time
import traceback
import threading
import winsound
from datetime import datetime

# BTC modules (run from BTC folder)
sys.path.insert(0, r"C:\Users\Karthick\BTC")
import importlib

# We import BTC modules directly (this file lives in BTC folder)
from data_fetcher import get_data as btc_get_data, get_session_info
from indicators import apply_indicators as btc_apply_indicators
from institutional_price_action import InstitutionalPriceActionSystem as BTC_IPA
from ipa_logger import IPALogger

# GOLD modules loaded via importlib to avoid namespace collision
import importlib.util

def _load(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_GOLD = r"C:\Users\Karthick\GOLD"
gold_fetcher    = _load("gold_data_fetcher",    f"{_GOLD}\\data_fetcher.py")
gold_indicators = _load("gold_indicators",      f"{_GOLD}\\indicators.py")
gold_ipa_mod    = _load("gold_ipa",             f"{_GOLD}\\institutional_price_action.py")

# ==========================================
# SOUND ALERTS
# ==========================================
def play_trade_alert():
    """Play 2 beeps when trade is taken"""
    try:
        winsound.Beep(1000, 200)  # 1000Hz for 200ms
        time.sleep(0.1)
        winsound.Beep(1000, 200)
    except:
        pass

def play_ready_alert():
    try:
        winsound.Beep(1200, 300)
        time.sleep(0.1)
        winsound.Beep(1200, 300)
        time.sleep(0.1)
        winsound.Beep(1500, 500)
    except:
        pass

# ==========================================
# LOGGER (shared across both symbols)
# ==========================================
ipa_logger = IPALogger()

# ==========================================
# SHARED STATE — thread-safe via lock
# ==========================================
results_lock = threading.Lock()
results = {
    "BTC":  {"setup": None, "price": 0, "active_trade": None, "trade_history": [], "error": None},
    "GOLD": {"setup": None, "price": 0, "active_trade": None, "trade_history": [], "error": None},
}

# ==========================================
# TRADE MONITOR (per symbol)
# ==========================================
def check_trade(sym, price):
    with results_lock:
        r = results[sym]
    t = r["active_trade"]
    if t is None:
        return

    entry, sl, tp = t["entry"], t["sl"], t["tp"]
    if t["direction"] == "BUY":
        pnl = price - entry
        tp_hit, sl_hit = price >= tp, price <= sl
    else:
        pnl = entry - price
        tp_hit, sl_hit = price <= tp, price >= sl

    pnl_pct = (pnl / entry) * 100
    if pnl > t.get("max_pnl", 0): t["max_pnl"] = pnl
    if pnl < t.get("min_pnl", 0): t["min_pnl"] = pnl

    if tp_hit or sl_hit:
        label = "TP" if tp_hit else "SL"
        elapsed = int((datetime.now() - t["entry_time"]).total_seconds() // 60)
        result_emoji = "🏆" if tp_hit else "💀"
        print(f"[{sym}] {result_emoji} {label} HIT | {t['direction']} @ ${entry:,.2f} → ${price:,.2f} | P&L: {pnl_pct:+.3f}% | {elapsed}min")
        t["result"] = label
        t["exit_price"] = price
        t["exit_time"] = datetime.now()
        t["final_pnl"] = pnl
        t["final_pnl_pct"] = pnl_pct
        ipa_logger.log_trade_exit(sym, t)
        with results_lock:
            results[sym]["trade_history"].append(t)
            results[sym]["active_trade"] = None

# ==========================================
# FORMAT SETUP BLOCK (per symbol)
# ==========================================
def format_block(sym):
    with results_lock:
        r = results[sym].copy()

    setup   = r["setup"]
    price   = r["price"]
    active  = r["active_trade"]
    history = r["trade_history"]
    err     = r["error"]

    sym_label = f"{'─'*20} {sym} {'─'*20}"

    if err:
        return f"\n{sym_label}\n❌ {err}\n"
    if setup is None:
        return f"\n{sym_label}\n⚠️ No data yet\n"

    direction = setup.get("signal", "NO TRADE")
    score     = setup.get("score", 0)
    ready     = setup.get("setup_ready", False)
    entry_p   = setup.get("entry", price)
    sl        = setup.get("sl", 0)
    tp        = setup.get("tp", 0)
    rr        = setup.get("rr", 0)
    trend_1h  = setup.get("trend", "NEUTRAL")
    struct_1h = setup.get("structure", "")
    session_i = setup.get("key_levels", {})
    cmet      = setup.get("conditions_met", [])
    cpend     = setup.get("conditions_pending", [])
    v_rev     = setup.get("v_reversal", {})
    m1h       = setup.get("momentum_1h", {})
    m5m       = setup.get("momentum_5m", {})
    ch        = setup.get("channel", {})
    ds        = setup.get("daily_supply")
    dd        = setup.get("daily_demand")
    sz        = setup.get("supply_zone")
    dz        = setup.get("demand_zone")

    action_map = {
        "SELL":       "🔴 ACTION: SELL NOW",
        "BUY":        "🟢 ACTION: BUY NOW",
        "WATCH_SELL": "🔴 ACTION: WAIT TO SELL",
        "WATCH_BUY":  "🟢 ACTION: WAIT TO BUY",
        "NEUTRAL":    "⚪ ACTION: NEUTRAL — WAIT",
        "NO TRADE":   "⚪ NO SETUP",
    }
    action = action_map.get(direction, f"⚪ {direction}")

    lines = [
        f"\n{'='*55}",
        f"  [ 🎯 {sym} PREDICTIVE SETUP ]",
        f"{'='*55}",
        f"{action}",
        f"Entry Readiness: {score}% | {'✅ READY' if ready else '⏳ FORMING'}",
        f"Entry: ${entry_p:,.2f}",
    ]
    if sl > 0: lines.append(f"SL: ${sl:,.2f}")
    if tp > 0: lines.append(f"TP: ${tp:,.2f}")
    if rr > 0: lines.append(f"R:R: {rr}")

    lines.append(f"1H Trend: {trend_1h} ({struct_1h})")
    lines.append(f"Momentum 1H: {m1h.get('momentum_state','N/A')} ({m1h.get('score','N/A')})")
    lines.append(f"Momentum 5m: {m5m.get('momentum_state','N/A')} ({m5m.get('score','N/A')})")

    if v_rev.get("pattern", "NONE") != "NONE":
        lines.append(f"V-Reversal: {v_rev['pattern']} at ${v_rev['reversal_level']:,.2f} ({v_rev['strength']}%)")

    if ch.get("type", "NONE") != "NONE":
        lines.append(f"Channel: {ch['type']} | Position: {ch.get('position',0):.0%} | Strength: {ch.get('strength',0)}%")

    if ds: lines.append(f"Daily Supply: ${ds[0]:,.2f}-${ds[1]:,.2f}")
    if dd: lines.append(f"Daily Demand: ${dd[0]:,.2f}-${dd[1]:,.2f}")
    if sz: lines.append(f"15m Supply Zone: ${sz[0]:,.2f}-${sz[1]:,.2f}")
    if dz: lines.append(f"15m Demand Zone: ${dz[0]:,.2f}-${dz[1]:,.2f}")

    # New patterns
    dp = setup.get("double_pattern", {})
    ib = setup.get("inside_bar", {})
    sp = setup.get("star_pattern", {})
    wk = setup.get("wyckoff", {})
    bk = setup.get("breaker", {})
    if dp.get("pattern", "NONE") != "NONE":
        lines.append(f"{dp['pattern']}: ${dp['level']:,.2f} | Neckline: ${dp.get('neckline',0):,.2f} ({dp['strength']}%)")
    if wk.get("pattern", "NONE") != "NONE":
        lines.append(f"{wk['pattern']}: ${wk['level']:,.2f} ({wk['strength']}%)")
    if ib.get("detected"):
        lines.append(f"Inside Bar x{ib['count']} ({ib['bias']}) | BO↑${ib['breakout_up']:,.2f} BO↓${ib['breakout_dn']:,.2f}")
    if sp.get("pattern", "NONE") != "NONE":
        lines.append(f"{sp['pattern']}: ${sp['level']:,.2f} ({sp['strength']}%)")
    if bk.get("bearish_breaker"):
        bb = bk["bearish_breaker"]
        lines.append(f"Bearish Breaker: ${bb['zone_low']:,.2f}-${bb['zone_high']:,.2f}")
    if bk.get("bullish_breaker"):
        bb = bk["bullish_breaker"]
        lines.append(f"Bullish Breaker: ${bb['zone_low']:,.2f}-${bb['zone_high']:,.2f}")

    if cmet:
        lines.append("✅ Confirmed:")
        for c in cmet:
            lines.append(f"   • {c}")
    if cpend:
        lines.append("⏳ Pending:")
        for c in cpend:
            lines.append(f"   • {c}")

    # Live trade monitor
    lines.append(f"\n{'─'*55}")
    lines.append("  [ 📡 LIVE TRADE MONITOR ]")
    lines.append(f"{'─'*55}")
    if active:
        t = active
        lp = (price - t["entry"]) if t["direction"] == "BUY" else (t["entry"] - price)
        lp_pct = (lp / t["entry"]) * 100
        elapsed = int((datetime.now() - t["entry_time"]).total_seconds() // 60)
        t_sl, t_tp = t["sl"], t["tp"]
        total_range = abs(t_tp - t_sl)
        if total_range > 0:
            if t["direction"] == "BUY":
                progress = (price - t_sl) / total_range * 100
            else:
                progress = (t_sl - price) / total_range * 100
            progress = max(0, min(100, progress))
        else:
            progress = 50
        bar_len = 20
        filled = int(progress / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        status = "🟢" if lp > 0 else "🔴"
        move = ("↑" if t["direction"] == "BUY" else "↓") if lp > 0 else ("↓" if t["direction"] == "BUY" else "↑")
        dist_tp = abs(t_tp - price)
        dist_sl = abs(price - t_sl)
        lines.append(f"  {t['direction']} | {elapsed}min in trade")
        lines.append(f"  Entry: ${t['entry']:,.2f}  →  Now: ${price:,.2f} {move}")
        lines.append(f"  {status} P&L: {lp:+.2f} ({lp_pct:+.3f}%)")
        lines.append(f"  SL ${t_sl:,.2f} [{bar}] TP ${t_tp:,.2f}")
        lines.append(f"  Progress: {progress:.0f}% | To TP: ${dist_tp:,.2f} | To SL: ${dist_sl:,.2f}")
        lines.append(f"  Peak: +${t.get('max_pnl',0):,.2f} | Worst: -${abs(t.get('min_pnl',0)):,.2f}")
    else:
        lines.append("  No active trade")

    wins    = sum(1 for x in history if x.get("result") == "TP")
    total   = len(history)
    pnl_sum = sum(x.get("final_pnl_pct", 0) for x in history)
    lines.append(f"{'─'*55}")
    lines.append(f"  Session: {wins}/{total} wins | P&L: {pnl_sum:+.3f}%")
    lines.append(f"{'='*55}")

    return "\n".join(lines)

# ==========================================
# SYMBOL WORKER THREAD
# ==========================================
def symbol_worker(sym, get_data_fn, apply_ind_fn, ipa_system, yahoo_sym):
    print(f"[{sym}] Worker started")
    while True:
        try:
            df = None
            for attempt in range(3):
                df = get_data_fn("5m", yahoo_sym) if sym == "GOLD" else get_data_fn("5m")
                if df is not None:
                    break
                print(f"[{sym}] ⚠️ Data fetch failed (attempt {attempt+1}/3), retrying in 10s...")
                time.sleep(10)

            if df is None:
                with results_lock:
                    results[sym]["error"] = "No data after 3 retries"
                time.sleep(30)
                continue

            df = apply_ind_fn(df)
            price = float(df.iloc[-1]["close"])

            df_1h  = df.attrs.get("df_1h")
            df_15m = df.attrs.get("df_15m")
            df_5m  = df.attrs.get("df_5m")
            df_1d  = df.attrs.get("df_1d")

            setup = None
            if df_1h is not None and df_15m is not None and df_5m is not None:
                setup = ipa_system.generate_predictive_setup(df_1h, df_15m, df_5m, df_1d)

            with results_lock:
                results[sym]["price"] = price
                results[sym]["setup"] = setup
                results[sym]["error"] = None

            # Check live trade SL/TP
            check_trade(sym, price)

            # Auto-enter trade when ready
            with results_lock:
                active = results[sym]["active_trade"]

            if setup and active is None:
                direction = setup.get("signal", "NO TRADE")
                ready     = setup.get("setup_ready", False)
                sl        = setup.get("sl", 0)
                tp        = setup.get("tp", 0)
                rr        = setup.get("rr", 0)
                score     = setup.get("score", 0)
                base_dir  = direction.replace("WATCH_", "")

                entry_p = setup.get("entry", price)
                if ready and sl > 0 and tp > 0 and sl != tp:
                    if base_dir == "BUY" and tp > sl:
                        trade = {"direction": "BUY", "entry": entry_p, "sl": sl, "tp": tp,
                                 "score": score, "entry_time": datetime.now(), "max_pnl": 0, "min_pnl": 0}
                        with results_lock:
                            results[sym]["active_trade"] = trade
                        play_trade_alert()
                        ipa_logger.log_trade_entry(sym, trade, setup)
                        print(f"[{sym}] 🚀 BUY READY | Entry: ${entry_p:,.2f} SL: ${sl:,.2f} TP: ${tp:,.2f}")

                    elif base_dir == "SELL" and tp < sl:
                        trade = {"direction": "SELL", "entry": entry_p, "sl": sl, "tp": tp,
                                 "score": score, "entry_time": datetime.now(), "max_pnl": 0, "min_pnl": 0}
                        with results_lock:
                            results[sym]["active_trade"] = trade
                        play_trade_alert()
                        ipa_logger.log_trade_entry(sym, trade, setup)
                        print(f"[{sym}] 🚀 SELL READY | Entry: ${entry_p:,.2f} SL: ${sl:,.2f} TP: ${tp:,.2f}")

            # Log every scan
            if setup:
                session_info = get_session_info()
                ipa_logger.log_scan(sym, setup, session_info.get("session", ""))

            print(f"[{sym}] ✅ Updated | ${price:,.2f} | {setup.get('signal','?') if setup else 'NO DATA'}")

        except Exception:
            print(f"[{sym}] ❌ Error:")
            traceback.print_exc()
            with results_lock:
                results[sym]["error"] = "Exception in worker"

        time.sleep(60)

# ==========================================
# MAIN BOT — starts both threads + Telegram loop
# ==========================================
def run_bot():
    print("\n🚀 BTC + GOLD PRICE ACTION BOT STARTED\n")

    btc_ipa  = BTC_IPA(symbol="BTCUSDT")
    gold_ipa = gold_ipa_mod.InstitutionalPriceActionSystem(symbol="XAUUSDT")

    # Start BTC worker
    t_btc = threading.Thread(
        target=symbol_worker,
        args=("BTC", btc_get_data, btc_apply_indicators, btc_ipa, "BTC-USD"),
        daemon=True
    )
    # Start GOLD worker
    t_gold = threading.Thread(
        target=symbol_worker,
        args=("GOLD", gold_fetcher.get_data, gold_indicators.apply_indicators, gold_ipa, "GC=F"),
        daemon=True
    )

    t_btc.start()
    time.sleep(30)   # stagger to avoid Yahoo rate-limit on parallel requests
    t_gold.start()

    session = get_session_info()
    iteration = 0

    while True:
        try:
            time.sleep(60)
            session = get_session_info()

            btc_block  = format_block("BTC")
            gold_block = format_block("GOLD")

            now = datetime.now().strftime("%H:%M:%S")
            tg_msg = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 {now} | {session['session']} | {session['priority']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{btc_block}

{gold_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

            # Print to console
            print(tg_msg)

            iteration += 1

        except KeyboardInterrupt:
            print("\n🛑 Bot stopped")
            break
        except Exception:
            traceback.print_exc()
            time.sleep(10)

# ==========================================
# START
# ==========================================
if __name__ == "__main__":
    run_bot()
