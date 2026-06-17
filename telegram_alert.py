import requests
import threading
from config import TELEGRAM_BOT, CHAT_ID


# ------------------------------------------
# 🔥 CORE SEND FUNCTION (SAFE)
# ------------------------------------------
def _send(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML"
            },
            timeout=5  # 🔥 CRITICAL: prevents freeze
        )

        # 🔍 Optional debug
        if response.status_code != 200:
            print("⚠️ Telegram failed:", response.text)

    except requests.exceptions.Timeout:
        print("⚠️ Telegram timeout")

    except requests.exceptions.ConnectionError:
        print("⚠️ Telegram connection error")

    except requests.exceptions.RequestException as e:
        print("⚠️ Telegram request error:", e)

    except Exception as e:
        print("⚠️ Unknown Telegram error:", e)


# ------------------------------------------
# � SEND FILE (CSV/TXT) VIA TELEGRAM
# ------------------------------------------
def _send_file(file_path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                url,
                data={"chat_id": CHAT_ID, "caption": caption},
                files={"document": f},
                timeout=30
            )
        if response.status_code != 200:
            print("⚠️ Telegram file send failed:", response.text)
        else:
            print(f"✅ File sent to Telegram: {file_path}")
    except Exception as e:
        print(f"⚠️ Telegram file send error: {e}")


def send_file(file_path, caption=""):
    try:
        threading.Thread(target=_send_file, args=(file_path, caption), daemon=True).start()
    except Exception as e:
        print("⚠️ File thread error:", e)


# ------------------------------------------
# �🚀 ASYNC SEND (NON-BLOCKING)
# ------------------------------------------
def send(msg):
    try:
        threading.Thread(target=_send, args=(msg,), daemon=True).start()
    except Exception as e:
        print("⚠️ Thread error:", e)