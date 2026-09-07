import os
import json
import subprocess
import requests
from datetime import datetime

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
STATE_FILE = "crt_state.json"

INTERVAL = "1d"

MARKETS = {
    "USDJPY": "USD/JPY",
    "EURJPY": "EUR/JPY",
    "GBPJPY": "GBP/JPY",
    "AUDJPY": "AUD/JPY",
    "CHFJPY": "CHF/JPY",
    "NZDJPY": "NZD/JPY",
    "CADJPY": "CAD/JPY",

    "AUDUSD": "AUD/USD",
    "EURAUD": "EUR/AUD",
    "GBPAUD": "GBP/AUD",
    "AUDCHF": "AUD/CHF",
    "AUDNZD": "AUD/NZD",
    "AUDCAD": "AUD/CAD",

    "USDCHF": "USD/CHF",
    "EURCHF": "EUR/CHF",
    "GBPCHF": "GBP/CHF",
    "NZDCHF": "NZD/CHF",
    "CADCHF": "CAD/CHF",

    "NZDUSD": "NZD/USD",
    "EURNZD": "EUR/NZD",
    "GBPNZD": "GBP/NZD",
    "NZDCAD": "NZD/CAD",

    "EURUSD": "EUR/USD",
    "EURGBP": "EUR/GBP",
    "EURCAD": "EUR/CAD",

    "GBPUSD": "GBP/USD",
    "GBPCAD": "GBP/CAD",

    "USDCAD": "USD/CAD",

    "XAUUSD": "Gold",
    "XAGUSD": "Silver",

    "US30": "US30",
    "USTEC": "US100",
    "US500": "US500",

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
            print(response.text)

    except Exception as e:
        print("❌ Discord connection error:", e)


def get_closed_candles(symbol):
    url = f"https://biquote.io/api/{symbol}/ohlc"

    response = requests.get(
        url,
        params={
            "interval": INTERVAL,
            "limit": 3
        },
        timeout=20
    )

    if response.status_code != 200:
        print("❌ API error:", symbol, response.status_code)
        return None

    data = response.json()

    closed = [
        bar for bar in data["bars"]
        if not bar["isOpen"]
    ]

    if len(closed) < 2:
        return None

    return closed


def check_crt(symbol):
    candles = get_closed_candles(symbol)

    if candles is None:
        return None

    current = candles[0]
    previous = candles[1]

    previous_high = float(previous["high"])
    previous_low = float(previous["low"])

    current_high = float(current["high"])
    current_low = float(current["low"])
    current_close = float(current["close"])

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
            ["git", "config", "user.email", "crt-bot@users.noreply.github.com"],
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
            ["git", "push"],
            check=True
        )

        print("✅ CRT state saved")

    except Exception as e:
        print("❌ Could not save state:", e)


print()
print("==============================================")
print("       🚨 CRT GITHUB DETECTOR")
print("==============================================")
print()
print("Markets:", len(MARKETS))
print("Timeframe: 1D")
print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()

state = load_state()

first_run = len(state) == 0

if first_run:
    print("🟡 FIRST RUN")
    print("Creating baseline.")
    print("Existing candles will NOT create alerts.")
    print()

alerts = 0

for symbol, display_name in MARKETS.items():

    try:
        candles = get_closed_candles(symbol)

        if candles is None:
            print("⚠️", display_name, "— data unavailable")
            continue

        current = candles[0]
        candle_time = current["openTime"]

        previous_time = state.get(symbol)

        if first_run:
            state[symbol] = candle_time
            print("✓ Baseline:", display_name)

            continue

        if previous_time == candle_time:
            print("•", display_name, "— already processed")
            continue

        print("🆕", display_name, "— new daily candle")

        signal = check_crt(symbol)

        state[symbol] = candle_time

        if signal == "SELL":

            message = (
                "🚨 CRT DETECTED\n\n"
                f"Pair: {display_name}\n"
                "SELL"
            )

            print("🚨 SELL:", display_name)
            send_discord(message)
            alerts += 1

        elif signal == "BUY":

            message = (
                "🚨 CRT DETECTED\n\n"
                f"Pair: {display_name}\n"
                "BUY"
            )

            print("🚨 BUY:", display_name)
            send_discord(message)
            alerts += 1

        else:
            print("✓", display_name, "— no CRT")

    except Exception as e:
        print("❌", display_name, "error:", e)


save_state(state)

if not first_run:
    git_save_state()

print()
print("==============================================")
print("Finished.")
print("Alerts sent:", alerts)
print("==============================================")
