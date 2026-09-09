import os
import json
import subprocess
import requests
from tradingview_sdk import TradingView, Interval
from datetime import datetime

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
STATE_FILE = "crt_state.json"

MARKETS = {
    "USDJPY": "OANDA:USDJPY",
    "EURJPY": "OANDA:EURJPY",
    "GBPJPY": "OANDA:GBPJPY",
    "AUDJPY": "OANDA:AUDJPY",
    "CHFJPY": "OANDA:CHFJPY",
    "NZDJPY": "OANDA:NZDJPY",
    "CADJPY": "OANDA:CADJPY",

    "AUDUSD": "OANDA:AUDUSD",
    "EURAUD": "OANDA:EURAUD",
    "GBPAUD": "OANDA:GBPAUD",
    "AUDCHF": "OANDA:AUDCHF",
    "AUDNZD": "OANDA:AUDNZD",
    "AUDCAD": "OANDA:AUDCAD",

    "USDCHF": "OANDA:USDCHF",
    "EURCHF": "OANDA:EURCHF",
    "GBPCHF": "OANDA:GBPCHF",
    "NZDCHF": "OANDA:NZDCHF",
    "CADCHF": "OANDA:CADCHF",

    "NZDUSD": "OANDA:NZDUSD",
    "EURNZD": "OANDA:EURNZD",
    "GBPNZD": "OANDA:GBPNZD",
    "NZDCAD": "OANDA:NZDCAD",

    "EURUSD": "OANDA:EURUSD",
    "EURGBP": "OANDA:EURGBP",
    "EURCAD": "OANDA:EURCAD",

    "GBPUSD": "OANDA:GBPUSD",
    "GBPCAD": "OANDA:GBPCAD",

    "USDCAD": "OANDA:USDCAD",

    "XAUUSD": "OANDA:XAUUSD",
    "XAGUSD": "OANDA:XAGUSD",

    "US30": "OANDA:US30USD",
    "USTEC": "OANDA:NAS100USD",
    "US500": "OANDA:SPX500USD",

    "BTCUSD": "OANDA:BTCUSD",
    "ETHUSD": "OANDA:ETHUSD",
}

DISPLAY_NAMES = {
    "XAUUSD": "Gold",
    "XAGUSD": "Silver",
    "USTEC": "US100",
    "BTCUSD": "Bitcoin",
    "ETHUSD": "Ethereum",
}

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def send_discord(message):
    try:
        response = requests.post(
            DISCORD_WEBHOOK,
            json={"content": message},
            timeout=20
        )

        if response.status_code in (200, 204):
            print("✅ Discord alert sent")
        else:
            print("❌ Discord error:", response.status_code)

    except Exception as e:
        print("❌ Discord connection error:", e)

def get_closed_candles(tv, symbol):
    bars = tv.get_bars(
        symbol,
        Interval.DAY,
        bars=3
    )

    if len(bars) < 2:
        return None

    return list(bars)[-2::-1][:2]

def check_crt(candles):
    current = candles[0]
    previous = candles[1]

    previous_high = float(previous.high)
    previous_low = float(previous.low)

    current_high = float(current.high)
    current_low = float(current.low)
    current_close = float(current.close)

    swept_high = current_high > previous_high
    swept_low = current_low < previous_low

    closed_inside = (
        current_close < previous_high
        and current_close > previous_low
    )

    if swept_high and closed_inside:
        return "SELL"

    if swept_low and closed_inside:
        return "BUY"

    return None

def git_save_state():

    try:
        subprocess.run(
            ["git", "config", "user.name", "CRT Bot"],
            check=True
        )

        subprocess.run(
            ["git", "config", "user.email",
             "crt-bot@users.noreply.github.com"],
            check=True
        )

        subprocess.run(
            ["git", "add", STATE_FILE],
            check=True
        )

        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"]
        )

        if result.returncode == 0:
            print("✓ No state changes to commit")
            return

        subprocess.run(
            ["git", "commit", "-m", "Update CRT detector state"],
            check=True
        )

        subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            check=True
        )

        subprocess.run(
            ["git", "push", "origin", "main"],
            check=True
        )

        print("✅ CRT state saved")

    except Exception as e:
        print("❌ Could not save state:", e)
