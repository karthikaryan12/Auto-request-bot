# ==========================================
# 🚀 INSTITUTIONAL DATA FETCHER V5
# SSL FIXED VERSION (WINDOWS STABLE)
# ==========================================

import ssl
import urllib3
import requests
import pandas as pd
import numpy as np

from datetime import datetime, timezone

# ==========================================
# SESSION FILTER
# Mentor: only trade London Open & NY Open
# London Open : 07:00 – 10:00 UTC
# NY Open     : 12:30 – 15:30 UTC
# Asian Range : 00:00 – 05:00 UTC (low priority)
# ==========================================
def get_session_info():
    now_utc = datetime.now(timezone.utc)
    hour    = now_utc.hour
    minute  = now_utc.minute
    decimal_hour = hour + minute / 60.0

    if 7.0 <= decimal_hour < 10.0:
        return {"session": "LONDON_OPEN",   "tradeable": True,  "priority": "HIGH"}
    elif 12.5 <= decimal_hour < 15.5:
        return {"session": "NY_OPEN",       "tradeable": True,  "priority": "HIGH"}
    elif 10.0 <= decimal_hour < 12.5:
        return {"session": "LONDON_NY_OVERLAP", "tradeable": True, "priority": "MEDIUM"}
    elif 0.0 <= decimal_hour < 5.0:
        return {"session": "ASIAN_RANGE",   "tradeable": False, "priority": "LOW"}
    else:
        return {"session": "OFF_HOURS",     "tradeable": False, "priority": "NONE"}

# ==========================================
# SSL FIX
# ==========================================

urllib3.disable_warnings()

ssl._create_default_https_context = (
    ssl._create_unverified_context
)

# ==========================================
# SESSION
# ==========================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ==========================================
# FETCH YAHOO DATA
# ==========================================

def fetch_yahoo(interval="5m"):

    try:

        url = (
            "https://query1.finance.yahoo.com/"
            "v8/finance/chart/BTC-USD"
        )

        # Use longer range for higher timeframes
        if interval == "1d":
            data_range = "6mo"
        elif interval in ["1h", "60m"]:
            data_range = "30d"
        else:
            data_range = "5d"

        params = {

            "range": data_range,

            "interval": interval
        }

        res = session.get(

            url,

            params=params,

            timeout=10,

            verify=False
        )

        if res.status_code != 200:

            print(
                f"❌ Yahoo HTTP Error ({interval})"
            )

            return None

        data = res.json()

        if (
            "chart" not in data
            or
            data["chart"]["result"] is None
        ):

            print(
                f"❌ Yahoo No Result ({interval})"
            )

            return None

        result = data["chart"]["result"][0]

        timestamps = result["timestamp"]

        ohlc = result["indicators"]["quote"][0]

        df = pd.DataFrame({

            "time":
            pd.to_datetime(
                timestamps,
                unit="s"
            ),

            "open":
            ohlc["open"],

            "high":
            ohlc["high"],

            "low":
            ohlc["low"],

            "close":
            ohlc["close"],

            "volume":
            ohlc["volume"]
        })

        df.dropna(inplace=True)

        # Filter zero volumes
        df = df[df["volume"] > 0]

        if len(df) < 30:

            print(
                f"❌ Insufficient Data ({interval})"
            )

            return None

        # ==========================================
        # EMA
        # ==========================================

        df["ema9"] = (
            df["close"]
            .ewm(span=9)
            .mean()
        )

        df["ema21"] = (
            df["close"]
            .ewm(span=21)
            .mean()
        )

        # ==========================================
        # VWAP
        # ==========================================

        typical_price = (

            df["high"]

            +

            df["low"]

            +

            df["close"]

        ) / 3

        df["vwap"] = (

            typical_price
            *
            df["volume"]

        ).cumsum() / (

            df["volume"]
            .cumsum()
        )

        # ==========================================
        # VOLUME
        # ==========================================

        df["vol_avg"] = (
            df["volume"]
            .rolling(20)
            .mean()
        )

        df["vol_ratio"] = (

            df["volume"]

            /

            (
                df["vol_avg"]
                + 1e-6
            )
        )

        # ==========================================
        # MOMENTUM
        # ==========================================

        df["momentum"] = (
            df["close"]
            .pct_change()
            * 100
        )

        return df

    except Exception as e:

        print(
            f"❌ Yahoo Error ({interval}):",
            e
        )

        return None

# ==========================================
# BINANCE OPEN INTEREST
# ==========================================

def get_binance_oi():

    try:

        url = (
            "https://fapi.binance.com/"
            "fapi/v1/openInterest"
        )

        params = {

            "symbol": "BTCUSDT"
        }

        res = session.get(

            url,

            params=params,

            timeout=10,

            verify=False
        )

        if res.status_code != 200:

            print(
                "❌ Binance OI HTTP Error"
            )

            return 0

        data = res.json()

        if "openInterest" not in data:

            return 0

        return float(
            data["openInterest"]
        )

    except Exception as e:

        print(
            "❌ Binance OI Error:",
            e
        )

        return 0

# ==========================================
# DERIBIT OI
# ==========================================

def get_deribit_oi():

    try:

        url = (
            "https://www.deribit.com/api/v2/"
            "public/get_book_summary_by_currency"
        )

        params = {

            "currency": "BTC",

            "kind": "option"
        }

        res = session.get(

            url,

            params=params,

            timeout=10,

            verify=False
        )

        if res.status_code != 200:

            print(
                "❌ Deribit HTTP Error"
            )

            return []

        data = res.json()

        if "result" not in data:

            return []

        result = data["result"]

        levels = []

        for item in result:

            instrument = item.get(
                "instrument_name",
                ""
            )

            oi = item.get(
                "open_interest",
                0
            )

            if oi <= 0:

                continue

            try:

                parts = instrument.split("-")

                strike = float(parts[2])

                option_type = parts[3]

                levels.append({

                    "strike":
                    strike,

                    "oi":
                    oi,

                    "type":
                    option_type
                })

            except:

                continue

        levels = sorted(

            levels,

            key=lambda x: x["oi"],

            reverse=True
        )

        return levels[:20]

    except Exception as e:

        print(
            "❌ Deribit Error:",
            e
        )

        return []

# ==========================================
# CPR
# ==========================================

def calculate_cpr(df):

    try:

        prev = df.iloc[-2]

        high = prev["high"]

        low = prev["low"]

        close = prev["close"]

        pivot = (
            high + low + close
        ) / 3

        bc = (
            high + low
        ) / 2

        tc = (
            pivot - bc
        ) + pivot

        width = abs(tc - bc)

        signal = "NORMAL"

        avg_range = (

            df["high"]

            -

            df["low"]

        ).rolling(20).mean().iloc[-1]

        if width < avg_range * 0.2:

            signal = "NARROW_BREAKOUT"

        elif width > avg_range * 0.6:

            signal = "SIDEWAYS"

        return {

            "pivot":
            round(pivot, 2),

            "tc":
            round(tc, 2),

            "bc":
            round(bc, 2),

            "width":
            round(width, 2),

            "signal":
            signal
        }

    except:

        return {

            "pivot": 0,

            "tc": 0,

            "bc": 0,

            "width": 0,

            "signal": "NORMAL"
        }

# ==========================================
# TREND DETECTOR
# ==========================================

def detect_tf_trend(df):

    try:

        last = df.iloc[-1]

        close = last["close"]

        ema9 = last["ema9"]

        ema21 = last["ema21"]

        vwap = last["vwap"]

        bullish = (

            close > ema9

            and

            ema9 > ema21

            and

            close > vwap
        )

        bearish = (

            close < ema9

            and

            ema9 < ema21

            and

            close < vwap
        )

        if bullish:

            return "BULLISH"

        elif bearish:

            return "BEARISH"

        return "SIDEWAYS"

    except:

        return "NEUTRAL"

# ==========================================
# PCR
# ==========================================

def calculate_pcr(oi_levels):

    try:

        call_oi = 0

        put_oi = 0

        for item in oi_levels:

            if item["type"] == "C":

                call_oi += item["oi"]

            elif item["type"] == "P":

                put_oi += item["oi"]

        if call_oi == 0:

            return 1

        pcr = put_oi / call_oi

        return round(pcr, 2)

    except:

        return 1

# ==========================================
# MAIN FETCHER
# ==========================================

def get_data(timeframe="5m"):

    try:

        # ==========================================
        # MULTI TIMEFRAME
        # ==========================================

        import time as _time
        df_1m = fetch_yahoo("1m");   _time.sleep(1)
        df_5m = fetch_yahoo("5m");   _time.sleep(1)
        df_15m = fetch_yahoo("15m"); _time.sleep(1)
        df_1h = fetch_yahoo("1h");   _time.sleep(1)
        df_1d = fetch_yahoo("1d")

        if (
            df_1m is None
            or
            df_5m is None
            or
            df_15m is None
            or
            df_1h is None
        ):

            print("❌ NO MARKET DATA")

            return None

        if df_1d is None:
            print("⚠️ Daily data unavailable — continuing without it")

        # ==========================================
        # SELECT TF
        # ==========================================

        if timeframe == "1m":

            df = df_1m

        elif timeframe == "15m":

            df = df_15m

        elif timeframe == "1h":

            df = df_1h

        else:

            df = df_5m

        last = df.iloc[-1]

        price = float(last["close"])

        volume = float(last["volume"])

        # ==========================================
        # OI
        # ==========================================

        oi_data = {}

        # ==========================================
        # DERIBIT
        # ==========================================

        oi_levels = get_deribit_oi()

        # ==========================================
        # PCR
        # ==========================================

        pcr = calculate_pcr(
            oi_levels
        )

        pcr_bias = "NEUTRAL"

        if pcr > 1.3:

            pcr_bias = "BULLISH"

        elif pcr < 0.7:

            pcr_bias = "BEARISH"

        print(f"📊 PCR: {pcr}  ->  PCR BIAS: {pcr_bias}")

        # ==========================================
        # CPR
        # ==========================================

        cpr_1m = calculate_cpr(df_1m)

        cpr_5m = calculate_cpr(df_5m)

        cpr_15m = calculate_cpr(df_15m)

        cpr_1h = calculate_cpr(df_1h)

        # ==========================================
        # TRENDS
        # ==========================================

        trend_1m = detect_tf_trend(df_1m)

        trend_5m = detect_tf_trend(df_5m)

        trend_15m = detect_tf_trend(df_15m)

        trend_1h = detect_tf_trend(df_1h)

        # ==========================================
        # STORE ATTRIBUTES
        # ==========================================

        df.attrs["oi_data"] = oi_data

        df.attrs["oi_levels"] = oi_levels

        df.attrs["pcr"] = pcr

        df.attrs["pcr_bias"] = pcr_bias

        df.attrs["trend_1m"] = trend_1m

        df.attrs["trend_5m"] = trend_5m

        df.attrs["trend_15m"] = trend_15m

        df.attrs["trend_1h"] = trend_1h

        df.attrs["cpr_1m"] = cpr_1m

        df.attrs["cpr_5m"] = cpr_5m

        df.attrs["cpr_15m"] = cpr_15m

        df.attrs["cpr_1h"] = cpr_1h

        df.attrs["timestamp"] = (
            datetime.now()
            .strftime("%H:%M:%S")
        )

        # ==========================================
        # STORE MULTI-TIMEFRAME DATAFRAMES
        # ==========================================
        df.attrs["df_1m"] = df_1m
        df.attrs["df_5m"] = df_5m
        df.attrs["df_15m"] = df_15m
        df.attrs["df_1h"] = df_1h
        df.attrs["df_1d"] = df_1d

        print("✅ MARKET DATA FETCHED")

        return df

    except Exception as e:

        print(
            "❌ DATA FETCHER ERROR:",
            e
        )

        return None

# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    df = get_data("5m")

    if df is not None:

        print("\n✅ FETCH SUCCESS")

        print(df.tail())

        print("\nPRICE:",
              round(df.iloc[-1]["close"], 2))

        print("PCR:",
              df.attrs["pcr"])

        print("PCR BIAS:",
              df.attrs["pcr_bias"])

        print("1M TREND:",
              df.attrs["trend_1m"])

        print("5M TREND:",
              df.attrs["trend_5m"])

        print("15M TREND:",
              df.attrs["trend_15m"])

        print("1H TREND:",
              df.attrs["trend_1h"])

    else:

        print("\n❌ NO DATA")