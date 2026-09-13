import os
import json
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
# SEPARATE 4H DISCORD WEBHOOK
# GitHub Secret:
# DISCORD_WEBHOOK_4H
# ============================================================

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_4H")


# ============================================================
# STATE FILE
# Remembers which 4H candle was already alerted
# ============================================================

STATE_FILE = "crt_state_4h.json"


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

        json.dump(
            state,
            f,
            indent=2
        )


# ============================================================
# SEND DISCORD ALERT
# ============================================================

def send_discord(message):

    if not DISCORD_WEBHOOK:

        print("❌ DISCORD_WEBHOOK_4H is missing")
        return False

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
            return True

        else:

            print(
                f"❌ Discord error: "
                f"{response.status_code} — "
                f"{response.text}"
            )

            return False

    except Exception as e:

        print(
            f"❌ Discord connection error: {e}"
        )

        return False


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
    # Liquidity sweeps
    # --------------------------------------------------------

    swept_high = current_high > previous_high
    swept_low = current_low < previous_low

    # --------------------------------------------------------
    # Current candle must close inside previous candle range
    # --------------------------------------------------------

    closed_inside = (
        current_close < previous_high
        and current_close > previous_low
    )

    # --------------------------------------------------------
    # HIGH SWEEP + CLOSE INSIDE = SELL
    # --------------------------------------------------------

    if swept_high and closed_inside:

        return "SELL"

    # --------------------------------------------------------
    # LOW SWEEP + CLOSE INSIDE = BUY
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

    # --------------------------------------------------------
    # Load previous alerts
    # --------------------------------------------------------

    state = load_state()

    signals = []

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

                # TradingView returns newest first
                current = bars[-1]
                previous = bars[-2]

                # ------------------------------------------------
                # Candle identification
                # ------------------------------------------------

                candle_time = str(current.datetime)

                print(
                    f"Current 4H: "
                    f"{candle_time}"
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
                # Check CRT
                # ------------------------------------------------

                signal = check_crt(
                    current,
                    previous
                )

                if not signal:

                    print("✓ No CRT")
                    continue

                # ------------------------------------------------
                # CHECK IF THIS CANDLE WAS ALREADY ALERTED
                # ------------------------------------------------

                last_alerted_candle = state.get(name)

                if last_alerted_candle == candle_time:

                    print(
                        "⚠️ CRT already alerted "
                        "for this 4H candle"
                    )

                    continue

                # ------------------------------------------------
                # NEW CRT
                # ------------------------------------------------

                print()
                print(
                    f"🚨 NEW CRT DETECTED: "
                    f"{signal}"
                )

                signals.append({
                    "pair": name,
                    "signal": signal,
                    "time": candle_time
                })

            except Exception as e:

                print(
                    f"❌ {name} — "
                    f"ERROR: {e}"
                )

    # ========================================================
    # SEND NEW SIGNALS
    # ========================================================

    print()
    print("==============================================")
    print("              FINAL RESULTS")
    print("==============================================")
    print()

    if signals:

        print(
            f"🚨 NEW CRT SIGNALS: "
            f"{len(signals)}"
        )

        print()

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

            # ------------------------------------------------
            # Only save the candle as alerted AFTER
            # Discord successfully receives the alert
            # ------------------------------------------------

            sent = send_discord(message)

            if sent:

                state[pair] = candle_time

                save_state(state)

                print(
                    f"💾 Saved state: "
                    f"{pair} → {candle_time}"
                )

    else:

        print(
            "No new CRT signals."
        )

    print()
    print("==============================================")
    print("Finished.")
    print("==============================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
