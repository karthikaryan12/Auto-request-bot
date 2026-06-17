import numpy as np
import pandas as pd


# ==========================================
# APPLY INDICATORS
# ==========================================
def apply_indicators(df):

    df = df.copy()

    # EMA
    df["ema9"] = df["close"].ewm(
        span=9,
        adjust=False
    ).mean()

    df["ema21"] = df["close"].ewm(
        span=21,
        adjust=False
    ).mean()

    # RSI
    delta = df["close"].diff()

    gain = delta.where(
        delta > 0,
        0
    )

    loss = -delta.where(
        delta < 0,
        0
    )

    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (
        avg_loss + 1e-9
    )

    df["rsi"] = 100 - (
        100 / (1 + rs)
    )

    # MACD
    ema12 = df["close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df["close"].ewm(
        span=26,
        adjust=False
    ).mean()

    df["macd"] = ema12 - ema26

    df["macd_signal"] = (
        df["macd"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )

    # ATR
    high_low = (
        df["high"]
        - df["low"]
    )

    high_close = (
        df["high"]
        - df["close"].shift()
    ).abs()

    low_close = (
        df["low"]
        - df["close"].shift()
    ).abs()

    tr = pd.concat(
        [
            high_low,
            high_close,
            low_close
        ],
        axis=1
    ).max(axis=1)

    df["atr"] = (
        tr.rolling(14)
        .mean()
    )

    # VWAP
    typical_price = (

        df["high"]

        +

        df["low"]

        +

        df["close"]

    ) / 3

    df["vwap"] = (

        typical_price
        * df["volume"]

    ).cumsum() / (

        df["volume"]
        .cumsum()
        + 1e-9
    )

    # Volume
    df["vol_avg"] = (
        df["volume"]
        .rolling(20)
        .mean()
    )

    df["vol_spike"] = (

        df["volume"]

        >

        df["vol_avg"] * 1.5
    )

    # Structure
    df["higher_low"] = (
        df["low"]
        >
        df["low"].shift(1)
    )

    df["lower_high"] = (
        df["high"]
        <
        df["high"].shift(1)
    )

    return df


# ==========================================
# ADX
# ==========================================
def calculate_adx(df):

    df = df.copy()

    high = df["high"]
    low = df["low"]
    close = df["close"]

    plus_dm = high.diff()

    minus_dm = -low.diff()

    plus_dm = np.where(
        (
            plus_dm > minus_dm
        )
        &
        (
            plus_dm > 0
        ),
        plus_dm,
        0
    )

    minus_dm = np.where(
        (
            minus_dm > plus_dm
        )
        &
        (
            minus_dm > 0
        ),
        minus_dm,
        0
    )

    tr1 = high - low

    tr2 = (
        high - close.shift()
    ).abs()

    tr3 = (
        low - close.shift()
    ).abs()

    tr = pd.concat(
        [
            tr1,
            tr2,
            tr3
        ],
        axis=1
    ).max(axis=1)

    atr = (
        tr.rolling(14)
        .mean()
    )

    plus_di = 100 * (

        pd.Series(plus_dm)
        .rolling(14)
        .mean()

        /

        (atr + 1e-9)
    )

    minus_di = 100 * (

        pd.Series(minus_dm)
        .rolling(14)
        .mean()

        /

        (atr + 1e-9)
    )

    dx = (

        abs(
            plus_di - minus_di
        )

        /

        (
            plus_di + minus_di
            + 1e-9
        )

    ) * 100

    df["+DI"] = plus_di

    df["-DI"] = minus_di

    df["adx"] = (
        dx.rolling(14)
        .mean()
    )

    # Compatibility
    df["ATR"] = df["atr"]
    df["ADX"] = df["adx"]

    return df