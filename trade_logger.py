import pandas as pd
import os
from datetime import datetime


class TradeLogger:

    def __init__(
        self,
        filename="trade_logs.csv"
    ):

        self.filename = filename

        if not os.path.exists(
            self.filename
        ):

            columns = [
                "timestamp",
                "price",
                "volume",
                "score",
                "required_score",
                "oi_state",
                "oi_bias",
                "oi_change",
                "oi_trend_strength",
                "market_pressure",
                "positioning",
                "liquidation_risk",
                "long_trap",
                "short_trap",
                "aggressive_longs",
                "aggressive_shorts",
                "oi_5m_change",
                "oi_15m_change",
                "oi_1h_change",
                "oi_velocity",
                "oi_acceleration",
                "pcr",
                "pcr_bias",
                "mtf_state",
                "mtf_bias",
                "trend_1m",
                "trend_5m",
                "trend_15m",
                "trend_1h",
                "market_regime",
                "impulse_direction",
                "impulse_score",
                "impulse_probability",
                "pullback_state",
                "pullback_score",
                "trap_type",
                "liquidity_state",
                "liquidity_score",
                "cpr_5m_signal",
                "cpr_15m_signal",
                "cpr_1h_signal",
                "cpr_score",
                "pcr_score",
                "volatility_score",
                "oi_strength",
                "structure_score",
                "target_score",
                "bull_probability",
                "bear_probability",
                "ai_market_bias",
                "ai_confidence",
                "support",
                "resistance",
                "atr",
                "signal",
                "direction",
                "entry",
                "stoploss",
                "target",
                "pressure_type",
                "pressure_strength",
                "breakout_stage",
                "breakout_probability",
                "ipa_signal",
                "ipa_score",
                "ipa_ready",
                "ipa_trend",
                "ipa_structure",
                "ipa_supply_zone",
                "ipa_demand_zone",
                "ipa_channel_type",
                "ipa_channel_position",
                "ipa_channel_upper",
                "ipa_channel_lower",
                "ipa_momentum_1h_score",
                "ipa_momentum_1h_state",
                "ipa_momentum_5m_score",
                "ipa_momentum_5m_state",
                "ipa_momentum_consec_bull",
                "ipa_momentum_consec_bear",
                "ipa_v_reversal_pattern",
                "ipa_v_reversal_strength",
                "ipa_v_reversal_level",
                "ipa_daily_supply",
                "ipa_daily_demand",
                "ipa_sl",
                "ipa_tp",
                "ipa_rr",
                "ipa_conditions_met",
                "ipa_conditions_pending"
            ]

            pd.DataFrame(
                columns=columns
            ).to_csv(
                self.filename,
                index=False
            )

        print(
            "[LOG] TRADE LOGGER READY"
        )

    def log_trade(

        self,

        price=0,

        volume=0,

        impulse=None,

        pullback=None,

        trap=None,

        oi=None,

        smart_money=None,

        regime=None,

        liquidity=None,

        trend_memory=None,

        execution=None,

        final_signal="NO TRADE",

        final_direction="NEUTRAL",

        entry=None,

        stoploss=None,

        target=None,

        ai_result=None,

        cpr_5m=None,

        cpr_15m=None,

        cpr_1h=None,

        trend_1m=None,

        trend_5m=None,

        trend_15m=None,

        trend_1h=None,

        support=None,

        resistance=None,

        atr=None,

        impulse_score=None,

        pullback_score=None,

        target_score=None,

        structure_score=None,

        liquidity_score=None,

        cpr_score=None,

        pcr_score=None,

        volatility_score=None,

        oi_strength=None,

        mtf_state=None,

        mtf_bias=None,

        required_score=None,

        pressure_type=None,

        pressure_strength=None,

        breakout_stage=None,

        breakout_probability=None,

        institutional_entry=None,

        predictive_setup=None,

        **kwargs
    ):

        try:

            row = {
                "timestamp":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "price":
                price,
                "volume":
                volume,
                "score":
                smart_money.get(
                    "score",
                    0
                ) if smart_money else 0,
                "required_score":
                required_score if required_score else 0,
                "oi_state":
                oi.get(
                    "oi_state",
                    "UNKNOWN"
                ) if oi else "UNKNOWN",
                "oi_bias":
                oi.get(
                    "oi_bias",
                    "UNKNOWN"
                ) if oi else "UNKNOWN",
                "oi_change":
                oi.get(
                    "oi_change",
                    0
                ) if oi else 0,
                "oi_trend_strength":
                oi.get(
                    "oi_trend_strength",
                    0
                ) if oi else 0,
                "market_pressure":
                oi.get(
                    "market_pressure",
                    "NEUTRAL"
                ) if oi else "NEUTRAL",
                "positioning":
                oi.get(
                    "positioning",
                    "NEUTRAL"
                ) if oi else "NEUTRAL",
                "liquidation_risk":
                oi.get(
                    "liquidation_risk",
                    "LOW"
                ) if oi else "LOW",
                "long_trap":
                oi.get(
                    "long_trap",
                    False
                ) if oi else False,
                "short_trap":
                oi.get(
                    "short_trap",
                    False
                ) if oi else False,
                "aggressive_longs":
                oi.get(
                    "aggressive_longs",
                    False
                ) if oi else False,
                "aggressive_shorts":
                oi.get(
                    "aggressive_shorts",
                    False
                ) if oi else False,
                "oi_5m_change":
                oi.get(
                    "oi_5m_change",
                    0
                ) if oi else 0,
                "oi_15m_change":
                oi.get(
                    "oi_15m_change",
                    0
                ) if oi else 0,
                "oi_1h_change":
                oi.get(
                    "oi_1h_change",
                    0
                ) if oi else 0,
                "oi_velocity":
                oi.get(
                    "oi_velocity",
                    0
                ) if oi else 0,
                "oi_acceleration":
                oi.get(
                    "oi_acceleration",
                    0
                ) if oi else 0,
                "pcr":
                smart_money.get(
                    "pcr",
                    0
                ) if smart_money else 0,
                "pcr_bias":
                smart_money.get(
                    "pcr_bias",
                    "NEUTRAL"
                ) if smart_money else "NEUTRAL",
                "mtf_state":
                mtf_state if mtf_state else "MIXED",
                "mtf_bias":
                mtf_bias if mtf_bias else "NEUTRAL",
                "trend_1m":
                trend_1m if trend_1m else "NEUTRAL",
                "trend_5m":
                trend_5m if trend_5m else "NEUTRAL",
                "trend_15m":
                trend_15m if trend_15m else "NEUTRAL",
                "trend_1h":
                trend_1h if trend_1h else "NEUTRAL",
                "market_regime":
                regime.get(
                    "regime",
                    "UNKNOWN"
                ) if regime else "UNKNOWN",
                "impulse_direction":
                impulse.get(
                    "direction",
                    "UNKNOWN"
                ) if impulse else "UNKNOWN",
                "impulse_score":
                impulse_score if impulse_score else 0,
                "impulse_probability":
                impulse.get(
                    "impulse_probability",
                    50
                ) if impulse else 50,
                "pullback_state":
                pullback.get(
                    "state",
                    "NONE"
                ) if pullback else "NONE",
                "pullback_score":
                pullback_score if pullback_score else 0,
                "trap_type":
                trap.get(
                    "type",
                    "NONE"
                ) if trap else "NONE",
                "liquidity_state":
                liquidity.get(
                    "state",
                    "UNKNOWN"
                ) if liquidity else "UNKNOWN",
                "liquidity_score":
                liquidity_score if liquidity_score else 0,
                "cpr_5m_signal":
                cpr_5m.get(
                    "signal",
                    "NORMAL"
                ) if cpr_5m else "NORMAL",
                "cpr_15m_signal":
                cpr_15m.get(
                    "signal",
                    "NORMAL"
                ) if cpr_15m else "NORMAL",
                "cpr_1h_signal":
                cpr_1h.get(
                    "signal",
                    "NORMAL"
                ) if cpr_1h else "NORMAL",
                "cpr_score":
                cpr_score if cpr_score else 0,
                "pcr_score":
                pcr_score if pcr_score else 0,
                "volatility_score":
                volatility_score if volatility_score else 0,
                "oi_strength":
                oi_strength if oi_strength else 0,
                "structure_score":
                structure_score if structure_score else 0,
                "target_score":
                target_score if target_score else 0,
                "bull_probability":
                ai_result.get(
                    "bull_probability",
                    50
                ) if ai_result else 50,
                "bear_probability":
                ai_result.get(
                    "bear_probability",
                    50
                ) if ai_result else 50,
                "ai_market_bias":
                ai_result.get(
                    "market_bias",
                    "NEUTRAL"
                ) if ai_result else "NEUTRAL",
                "ai_confidence":
                ai_result.get(
                    "confidence",
                    50
                ) if ai_result else 50,
                "support":
                support if support else 0,
                "resistance":
                resistance if resistance else 0,
                "atr":
                atr if atr else 0,
                "signal":
                final_signal,
                "direction":
                final_direction,
                "entry":
                entry,
                "stoploss":
                stoploss,
                "target":
                target,
                "pressure_type":
                pressure_type if pressure_type else "NONE",
                "pressure_strength":
                pressure_strength if pressure_strength else 0,
                "breakout_stage":
                breakout_stage if breakout_stage else "NONE",
                "breakout_probability":
                breakout_probability if breakout_probability else 0,
                "ipa_signal":
                predictive_setup.get("signal", "NONE") if predictive_setup else "NONE",
                "ipa_score":
                predictive_setup.get("score", 0) if predictive_setup else 0,
                "ipa_ready":
                predictive_setup.get("setup_ready", False) if predictive_setup else False,
                "ipa_trend":
                predictive_setup.get("trend", "NEUTRAL") if predictive_setup else "NEUTRAL",
                "ipa_structure":
                predictive_setup.get("structure", "UNKNOWN") if predictive_setup else "UNKNOWN",
                "ipa_supply_zone":
                str(predictive_setup.get("supply_zone", "")) if predictive_setup else "",
                "ipa_demand_zone":
                str(predictive_setup.get("demand_zone", "")) if predictive_setup else "",
                "ipa_channel_type":
                predictive_setup.get("channel", {}).get("type", "NONE") if predictive_setup else "NONE",
                "ipa_channel_position":
                predictive_setup.get("channel", {}).get("position", 0) if predictive_setup else 0,
                "ipa_channel_upper":
                predictive_setup.get("channel", {}).get("upper", 0) if predictive_setup else 0,
                "ipa_channel_lower":
                predictive_setup.get("channel", {}).get("lower", 0) if predictive_setup else 0,
                "ipa_momentum_1h_score":
                predictive_setup.get("momentum_1h", {}).get("score", 0) if predictive_setup else 0,
                "ipa_momentum_1h_state":
                predictive_setup.get("momentum_1h", {}).get("momentum_state", "NEUTRAL") if predictive_setup else "NEUTRAL",
                "ipa_momentum_5m_score":
                predictive_setup.get("momentum_5m", {}).get("score", 0) if predictive_setup else 0,
                "ipa_momentum_5m_state":
                predictive_setup.get("momentum_5m", {}).get("momentum_state", "NEUTRAL") if predictive_setup else "NEUTRAL",
                "ipa_momentum_consec_bull":
                predictive_setup.get("momentum_1h", {}).get("consecutive_bullish", 0) if predictive_setup else 0,
                "ipa_momentum_consec_bear":
                predictive_setup.get("momentum_1h", {}).get("consecutive_bearish", 0) if predictive_setup else 0,
                "ipa_v_reversal_pattern":
                predictive_setup.get("v_reversal", {}).get("pattern", "NONE") if predictive_setup else "NONE",
                "ipa_v_reversal_strength":
                predictive_setup.get("v_reversal", {}).get("strength", 0) if predictive_setup else 0,
                "ipa_v_reversal_level":
                predictive_setup.get("v_reversal", {}).get("reversal_level", 0) if predictive_setup else 0,
                "ipa_daily_supply":
                str(predictive_setup.get("daily_supply", "")) if predictive_setup else "",
                "ipa_daily_demand":
                str(predictive_setup.get("daily_demand", "")) if predictive_setup else "",
                "ipa_sl":
                predictive_setup.get("sl", 0) if predictive_setup else 0,
                "ipa_tp":
                predictive_setup.get("tp", 0) if predictive_setup else 0,
                "ipa_rr":
                predictive_setup.get("rr", 0) if predictive_setup else 0,
                "ipa_conditions_met":
                "; ".join(predictive_setup.get("conditions_met", [])) if predictive_setup else "",
                "ipa_conditions_pending":
                "; ".join(predictive_setup.get("conditions_pending", [])) if predictive_setup else ""
            }

            pd.DataFrame(
                [row]
            ).to_csv(

                self.filename,

                mode="a",

                header=False,

                index=False
            )

            print(
                f"📝 TRADE LOGGED: "
                f"{final_signal}"
            )

        except Exception as e:

            print(
                "❌ LOGGER ERROR:",
                e
            )
