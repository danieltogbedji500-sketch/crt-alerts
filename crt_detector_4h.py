import os
import requests
from tradingview_sdk import TradingView


# ============================================================
# 4H CRT DETECTOR
# TradingView OANDA Feed
# ============================================================

MARKETS = {

    # ==================== US INDICES ====================

    "US30": "OANDA:US30USD",
    "US100": "OANDA:NAS100USD",
    "US500": "OANDA:SPX500USD",
    "US2000": "OANDA:US2000USD",

    # ==================== EUROPE ====================

    "GER40": "OANDA:DE30EUR",
    "UK100": "OANDA:UK100GBP",
    "FRA40": "OANDA:FR40EUR",
    "EU50": "OANDA:EU50EUR",
    "CH20": "OANDA:CH20CHF",

    # ==================== ASIA / PACIFIC ====================

    "JP225": "OANDA:JP225USD",
    "HK33": "OANDA:HK33HKD",
    "AU200": "OANDA:AU200AUD",

    # ==================== METALS ====================

    "Gold": "OANDA:XAUUSD",
    "Silver": "OANDA:XAGUSD",

    # ==================== CRYPTO ====================

    "Bitcoin": "OANDA:BTCUSD",
    "Ethereum": "OANDA:ETHUSD",
}


# ============================================================
# DISCORD WEBHOOK
# IMPORTANT:
# This is a SEPARATE webhook from the 1D detector.
# GitHub Secret name:
# DISCORD_WEBHOOK_4H
# ============================================================

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_4H")


# ============================================================
# SEND DISCORD ALERT
# ============================================================

def send_discord(message):

    if not DISCORD_WEBHOOK:
        print("❌ DISCORD_WEBHOOK_4H is missing")
        return

    try:

        response = requests.post(
            DISCORD_WEBHOOK,
            json={
                "content": message
            },
            timeout=20
        )

        if response.status_code in (200, 204):

            print("✅ Discord alert sent")

        else:

            print(
                f"❌ Discord error: "
                f"{response.status_code} — "
                f"{response.text}"
            )

    except Exception as e:

        print(f"❌ Discord connection error: {e}")


# ============================================================
# CRT LOGIC
# ============================================================

def check_crt(current, previous):

    previous_high = float(previous.high)
    previous_low = float(previous.low)

    current_high = float(current.high)
    current_low = float(current.low)
    current_close = float(current.close)

    # --------------------------------------------------------
    # Check liquidity sweep
    # --------------------------------------------------------

    swept_high = current_high > previous_high
    swept_low = current_low < previous_low

    # --------------------------------------------------------
    # Candle must close INSIDE previous candle range
    # --------------------------------------------------------

    closed_inside = (
        current_close < previous_high
        and current_close > previous_low
    )

    # --------------------------------------------------------
    # HIGH SWEEP + CLOSE INSIDE = SELL CRT
    # --------------------------------------------------------

    if swept_high and closed_inside:

        return "SELL"

    # --------------------------------------------------------
    # LOW SWEEP + CLOSE INSIDE = BUY CRT
    # --------------------------------------------------------

    if swept_low and closed_inside:

        return "BUY"

    return None


# ============================================================
# MAIN DETECTOR
# ============================================================

def main():

    print("==============================================")
    print("          🚨 4H CRT DETECTOR")
    print("==============================================")
    print()

    print(f"Markets: {len(MARKETS)}")
    print("Timeframe: 4H")
    print("Feed: TradingView OANDA")
    print()

    signals = []

    # --------------------------------------------------------
    # Connect to TradingView
    # --------------------------------------------------------

    with TradingView() as tv:

        for name, symbol in MARKETS.items():

            try:

                print("----------------------------------------------")
                print(f"Checking: {name}")

                # 240 = 4 HOURS
                bars = list(
                    tv.get_bars(
                        symbol,
                        "240",
                        bars=5
                    )
                )

                if len(bars) < 2:

                    print(
                        f"❌ {name} — "
                        "not enough data"
                    )

                    continue

                # TradingView returns newest first.
                # The last two bars are the latest candles.

                current = bars[-1]
                previous = bars[-2]

                signal = check_crt(
                    current,
                    previous
                )

                print(
                    f"Current 4H: "
                    f"{current.datetime}"
                )

                print(
                    f"O: {current.open} | "
                    f"H: {current.high} | "
                    f"L: {current.low} | "
                    f"C: {current.close}"
                )

                print(
                    f"Previous H: {previous.high} | "
                    f"Previous L: {previous.low}"
                )

                # ------------------------------------------------
                # CRT FOUND
                # ------------------------------------------------

                if signal:

                    print()
                    print(
                        f"🚨 CRT DETECTED: "
                        f"{signal}"
                    )

                    signals.append({
                        "pair": name,
                        "signal": signal,
                        "time": str(current.datetime)
                    })

                else:

                    print("✓ No CRT")

            except Exception as e:

                print(
                    f"❌ {name} — "
                    f"ERROR: {e}"
                )

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print()
    print("==============================================")
    print("              FINAL RESULTS")
    print("==============================================")
    print()

    if signals:

        print(
            f"🚨 CRT SIGNALS FOUND: "
            f"{len(signals)}"
        )

        print()

        # ----------------------------------------------------
        # Send every signal to Discord
        # ----------------------------------------------------

        for signal in signals:

            pair = signal["pair"]
            direction = signal["signal"]
            candle_time = signal["time"]

            message = (
                "🚨 **CRT DETECTED**\n\n"
                f"Pair: **{pair}**\n"
                f"**{direction}**\n"
                "Timeframe: **4H**\n"
                f"Time: `{candle_time}`"
            )

            print(
                f"🚨 {pair} — "
                f"{direction} — "
                f"{candle_time}"
            )

            send_discord(message)

    else:

        print(
            "No CRT detected on "
            "the latest 4H candles."
        )

    print()
    print("==============================================")
    print("Finished.")
    print("==============================================")


# ============================================================
# RUN DETECTOR
# ============================================================

if __name__ == "__main__":

    main()
