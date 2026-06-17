# ==========================================
# 🔥 CONFIG FILE (CRYPTO VERSION)
# ==========================================

# -------- ASSET CONFIG --------
ASSET = "BTC"
SYMBOL = "BTCUSDT"        # Binance symbol
YAHOO_SYMBOL = "BTC-USD" # For price data

# -------- BINANCE --------
BINANCE_BASE_URL = "https://fapi.binance.com"

# (No API key needed for public OI endpoint)

# -------- TELEGRAM --------
TELEGRAM_BOT = "8245901834:AAEIhQ8Y5VjXqaNhtcI3orpPsswRFDJxVes"
CHAT_ID = "717504934"

# -------- SYSTEM SETTINGS --------
TIMEOUT = 10
RETRY_COUNT = 3
SLEEP_INTERVAL = 10   # Faster for crypto (24/7)

# -------- TRADING PARAMS --------
VOLATILITY_MULTIPLIER = 0.8   # used in target engine
OI_SENSITIVITY = 1.0          # adjust later if needed