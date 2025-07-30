# main.py
import time
import traceback
from strategy import SmartEntryStrategy
from my_bingx_api import BingxClient
from indicators import Indicators
from config import config
from data_feed import fetch_ohlcv
from log_manager import log_info, log_error
from memory import initialize_recent_wins
from ai_module import get_adjust_factor

# === CONFIGURATION API ===
API_KEY = "TON_API_KEY"
API_SECRET = "TON_API_SECRET"

# === INITIALISATION DU FICHIER DE MÉMOIRE ===
initialize_recent_wins()

# === INITIALISATION STRATÉGIE ===
config['initial_equity'] = 120
symbol = config['symbol']
strategy = SmartEntryStrategy(API_KEY, API_SECRET)
bingx = BingxClient(API_KEY, API_SECRET)

# === PARAMÈTRES ===
M3_INTERVAL = 180
last_m3_refresh = 0
latest_candle = None

# === TRAILING STATE ===
in_position = False
entry_price = None
side = None
trailing_stop = None
trailing_offset = None
trailing_sl = None

def run_bot():
    global last_m3_refresh, latest_candle
    global in_position, entry_price, side, trailing_stop, trailing_offset, trailing_sl

    log_info("🚀 Bot lancé avec trailing stop manuel actif")

    while True:
        try:
            now = time.time()

            # === 1. Vérifie TP/SL avec le système de la stratégie ===
            if strategy.pm.entry_time is not None:
                log_info("🔄 Vérification TP/SL...")
                try:
                    current_price = bingx.get_entry_price(symbol)
                    strategy.pm.check_exit_conditions(
                        entry_price=current_price,
                        tp=strategy.pm.tp_target,
                        sl=strategy.pm.sl_target,
                        side=strategy.pm.current_side
                    )
                except Exception as e:
                    log_error(f"Erreur TP/SL : {e}")

            # === 2. Gestion du trailing stop manuel toutes les secondes ===
            if in_position and trailing_stop is not None and trailing_offset is not None:
                try:
                    current_price = bingx.get_entry_price(symbol)

                    if side == "BUY":
                        new_sl = current_price - (trailing_stop + trailing_offset)
                        if new_sl > trailing_sl:
                            trailing_sl = new_sl
                            log_info(f"[TRAIL] Nouveau SL (long): {trailing_sl:.2f}")
                        elif current_price < trailing_sl:
                            log_info(f"[TRAIL] 💥 Stop touché (long). Fermeture à {current_price}")
                            bingx.close_market_order(symbol, side)
                            in_position = False
                            trailing_sl = None
                    else:
                        new_sl = current_price + (trailing_stop + trailing_offset)
                        if new_sl < trailing_sl:
                            trailing_sl = new_sl
                            log_info(f"[TRAIL] Nouveau SL (short): {trailing_sl:.2f}")
                        elif current_price > trailing_sl:
                            log_info(f"[TRAIL] 💥 Stop touché (short). Fermeture à {current_price}")
                            bingx.close_market_order(symbol, side)
                            in_position = False
                            trailing_sl = None

                except Exception as e:
                    log_error(f"Erreur trailing stop : {e}")

            # === 3. Récupère les bougies toutes les 3 minutes ===
            if now - last_m3_refresh > M3_INTERVAL:
                log_info("📡 Récupération des bougies M3...")
                candles = fetch_ohlcv(symbol.replace("-", "/"), timeframe="3m", limit=150)

                if candles:
                    formatted = [{
                        "timestamp": c[0],
                        "open": c[1],
                        "high": c[2],
                        "low": c[3],
                        "close": c[4],
                        "volume": c[5]
                    } for c in candles]

                    latest_candle = formatted
                    last_m3_refresh = now
                    log_info("✅ Bougies M3 mises à jour")
                else:
                    log_info("⚠️ Impossible de récupérer les bougies")

            # === 4. Analyse toutes les secondes si pas de position ===
            if strategy.pm.entry_time is None and not in_position and latest_candle:
                log_info("🔍 Analyse en cours du marché...")
                try:
                    live_price = bingx.get_entry_price(symbol)
                    modified = latest_candle.copy()
                    modified[-1]["close"] = live_price

                    signal = strategy.on_new_candle(modified)

                    if signal and signal.get("side") and signal.get("qty"):
                        log_info(f"🟢 Signal détecté : {signal}")

                        # ✅ Ajustement dynamique du TP/SL
                        adjust_factor = get_adjust_factor()
                        signal["tp"] *= adjust_factor
                        signal["sl"] *= adjust_factor

                        bingx.place_order_with_protection(
                        symbol=symbol,
                        side=signal["side"],
                        quantity=signal["qty"],
                        tp=signal.get("tp"),
                        sl=signal.get("sl"),
                        trailing_stop=signal.get("trailing_stop"),
                        trailing_offset=signal.get("trailing_offset")
                        )

                        # 🔐 Enregistre les paramètres de position
                        in_position = True
                        entry_price = live_price
                        side = signal["side"]
                        trailing_stop = signal.get("trailing_stop", 0.5)
                        trailing_offset = signal.get("trailing_offset", 0.2)
                        trailing_sl = entry_price - (trailing_stop + trailing_offset) if side == "BUY" else entry_price + (trailing_stop + trailing_offset)

                except Exception as e:
                    log_error(f"Erreur d’analyse ou exécution : {e}")

        except Exception as e:
            log_error(f"💥 Erreur critique dans la boucle principale : {e}")
            traceback.print_exc()

        time.sleep(1)

if __name__ == "__main__":
    run_bot()
