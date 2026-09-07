import requests
import time
from datetime import datetime

# ============================================================
#                    SETTINGS
# ============================================================

DISCORD_WEBHOOK = "PASTE_YOUR_DISCORD_WEBHOOK_URL_HERE"

INTERVAL = "1d"

# Check the markets every 3 hours
CHECK_EVERY_SECONDS = 3 * 60 * 60


# ============================================================
#                    MARKETS
# ============================================================

MARKETS = {

    # =========================
    # JPY
    # =========================
    "USDJPY": "USD/JPY",
    "EURJPY": "EUR/JPY",
    "GBPJPY": "GBP/JPY",
    "AUDJPY": "AUD/JPY",
    "CHFJPY": "CHF/JPY",
    "NZDJPY": "NZD/JPY",
    "CADJPY": "CAD/JPY",

    # =========================
    # AUD
    # =========================
    "AUDUSD": "AUD/USD",
    "EURAUD": "EUR/AUD",
    "GBPAUD": "GBP/AUD",
    "AUDCHF": "AUD/CHF",
    "AUDNZD": "AUD/NZD",
    "AUDCAD": "AUD/CAD",

    # =========================
    # CHF
    # =========================
    "USDCHF": "USD/CHF",
    "EURCHF": "EUR/CHF",
    "GBPCHF": "GBP/CHF",
    "NZDCHF": "NZD/CHF",
    "CADCHF": "CAD/CHF",

    # =========================
    # NZD
    # =========================
    "NZDUSD": "NZD/USD",
    "EURNZD": "EUR/NZD",
    "GBPNZD": "GBP/NZD",
    "NZDCAD": "NZD/CAD",

    # =========================
    # EUR
    # =========================
    "EURUSD": "EUR/USD",
    "EURGBP": "EUR/GBP",
    "EURCAD": "EUR/CAD",

    # =========================
    # GBP
    # =========================
    "GBPUSD": "GBP/USD",
    "GBPCAD": "GBP/CAD",

    # =========================
    # CAD
    # =========================
    "USDCAD": "USD/CAD",

    # =========================
    # METALS
    # =========================
    "XAUUSD": "Gold",
    "XAGUSD": "Silver",

    # =========================
    # INDICES
    # =========================
    "US30": "US30",
    "USTEC": "US100",
    "US500": "US500",

    # =========================
    # CRYPTO
    # =========================
    "BTCUSD": "Bitcoin",
    "ETHUSD": "Ethereum",
}


# ============================================================
#                 DISCORD FUNCTION
# ============================================================

def send_discord(message):

    try:

        response = requests.post(
            DISCORD_WEBHOOK,
            json={"content": message},
            timeout=20
        )

        if response.status_code in [200, 204]:

            print("✅ Discord alert sent")

        else:

            print(
                "❌ Discord error:",
                response.status_code
            )

            print(response.text)

    except Exception as e:

        print(
            "❌ Discord connection error:",
            e
        )


# ============================================================
#                GET CLOSED DAILY CANDLES
# ============================================================

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

        print(
            "❌ API error:",
            symbol,
            response.status_code
        )

        return None

    data = response.json()

    closed = [
        bar for bar in data["bars"]
        if not bar["isOpen"]
    ]

    if len(closed) < 2:

        return None

    return closed


# ============================================================
#                    CRT CHECK
# ============================================================

def check_crt(symbol, display_name):

    candles = get_closed_candles(symbol)

    if candles is None:

        return None

    # Latest completed candle
    current = candles[0]

    # Candle immediately before it
    previous = candles[1]

    candle_time = current["openTime"]

    # Previous candle range
    previous_high = float(previous["high"])
    previous_low = float(previous["low"])

    # Current candle
    current_high = float(current["high"])
    current_low = float(current["low"])
    current_close = float(current["close"])


    # ========================================================
    #                    SWEEPS
    # ========================================================

    swept_high = current_high > previous_high

    swept_low = current_low < previous_low


    # ========================================================
    #             CLOSE BACK INSIDE RANGE
    # ========================================================

    closed_inside = (
        current_close < previous_high
        and
        current_close > previous_low
    )


    # ========================================================
    #                    SELL CRT
    # ========================================================

    if swept_high and closed_inside:

        return {
            "type": "SELL",
            "symbol": symbol,
            "name": display_name,
            "time": candle_time
        }


    # ========================================================
    #                     BUY CRT
    # ========================================================

    if swept_low and closed_inside:

        return {
            "type": "BUY",
            "symbol": symbol,
            "name": display_name,
            "time": candle_time
        }


    # No CRT
    return {
        "type": None,
        "symbol": symbol,
        "name": display_name,
        "time": candle_time
    }


# ============================================================
#                 STARTUP BASELINE
# ============================================================

last_processed = {}

print()
print("================================================")
print("          CRT MULTI-MARKET DETECTOR")
print("================================================")
print()

print("Markets:", len(MARKETS))
print("Timeframe: 1D")
print("Check interval: EVERY 3 HOURS")
print("Discord alerts: ON")
print()

print("Creating startup baseline...")
print()
print("Existing candles will NOT create alerts.")
print()


# ============================================================
#          CREATE INITIAL BASELINE
# ============================================================

for symbol, display_name in MARKETS.items():

    try:

        candles = get_closed_candles(symbol)

        if candles:

            last_processed[symbol] = candles[0]["openTime"]

            print(
                "✅ Baseline:",
                symbol
            )

        else:

            print(
                "⚠️ Baseline unavailable:",
                symbol
            )

    except Exception as e:

        print(
            "❌ Baseline error:",
            symbol,
            e
        )


# ============================================================
#                    START
# ============================================================

print()
print("================================================")
print("       🚨 CRT DETECTOR IS NOW RUNNING")
print("================================================")
print()

print("Monitoring", len(MARKETS), "markets")
print("Waiting for new daily candle closes...")
print()
print("Next check in 3 hours.")
print()


# ============================================================
#                    MAIN LOOP
# ============================================================

while True:

    try:

        print()
        print(
            "🔎 Checking all markets:",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        print()


        # ====================================================
        #                 CHECK EACH MARKET
        # ====================================================

        for symbol, display_name in MARKETS.items():

            try:

                result = check_crt(
                    symbol,
                    display_name
                )

                if result is None:

                    print(
                        "⚠️",
                        symbol,
                        "— data unavailable"
                    )

                    continue


                candle_time = result["time"]


                # =================================================
                #            IS THIS A NEW DAILY CANDLE?
                # =================================================

                if (
                    symbol not in last_processed
                    or
                    candle_time != last_processed[symbol]
                ):

                    # Mark it as processed
                    last_processed[symbol] = candle_time


                    # =============================================
                    #                    SELL
                    # =============================================

                    if result["type"] == "SELL":

                        message = (
                            "🚨 CRT DETECTED\n\n"
                            f"Pair: {display_name}\n"
                            "SELL"
                        )

                        print()
                        print(
                            "================================"
                        )
                        print("🚨 CRT DETECTED")
                        print()
                        print(
                            "Pair:",
                            display_name
                        )
                        print("SELL")
                        print(
                            "Candle:",
                            candle_time
                        )
                        print(
                            "================================"
                        )
                        print()

                        send_discord(message)


                    # =============================================
                    #                     BUY
                    # =============================================

                    elif result["type"] == "BUY":

                        message = (
                            "🚨 CRT DETECTED\n\n"
                            f"Pair: {display_name}\n"
                            "BUY"
                        )

                        print()
                        print(
                            "================================"
                        )
                        print("🚨 CRT DETECTED")
                        print()
                        print(
                            "Pair:",
                            display_name
                        )
                        print("BUY")
                        print(
                            "Candle:",
                            candle_time
                        )
                        print(
                            "================================"
                        )
                        print()

                        send_discord(message)


                    # =============================================
                    #                  NO CRT
                    # =============================================

                    else:

                        print(
                            "✓",
                            symbol,
                            "— new candle, no CRT"
                        )


                else:

                    print(
                        "•",
                        symbol,
                        "— waiting"
                    )


            except Exception as e:

                print(
                    "❌",
                    symbol,
                    "error:",
                    e
                )


        # ====================================================
        #                 WAIT 3 HOURS
        # ====================================================

        print()
        print("================================================")
        print("Finished checking all markets.")
        print("Sleeping for 3 HOURS...")
        print("================================================")
        print()

        time.sleep(
            CHECK_EVERY_SECONDS
        )


    except Exception as e:

        print()
        print(
            "❌ MAIN LOOP ERROR:",
            e
        )
        print("Retrying in 1 minute...")
        print()

        time.sleep(60)
