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

# === CONFIGURATION API ===
API_KEY = "TON_API_KEY"
API_SECRET = "TON_API_SECRET"

# === INITIALISATION DU FICHIER DE MÉMOIRE ===
initialize_recent_wins()  # Initialise le fichier recent_trades.json si besoin

# === INITIALISATION STRATÉGIE ===
config['initial_equity'] = 120
symbol = config['symbol']
strategy = SmartEntryStrategy(API_KEY, API_SECRET)
bingx = BingxClient(API_KEY, API_SECRET)

# === PARAMÈTRES ===
M3_INTERVAL = 180  # 3 minutes
last_m3_refresh = 0
latest_candle = None

def run_bot():
    global last_m3_refresh, latest_candle
    log_info("🚀 Bot lancé avec surveillance live chaque seconde (sans Supabase)")

    while True:
        try:
            now = time.time()

            # === 1. Vérifie TP / SL si position ouverte ===
            if strategy.pm.entry_time is not None:
                log_info("🔄 Vérification TP/SL en cours...")
                try:
                    entry_price = bingx.get_entry_price(symbol)
                    strategy.pm.check_exit_conditions(
                        entry_price=entry_price,
                        tp=strategy.pm.tp_target,
                        sl=strategy.pm.sl_target,
                        side=strategy.pm.current_side
                    )
                except Exception as e:
                    log_error(f"Erreur vérification TP/SL : {e}", e)

            # === 2. Récupère les bougies toutes les 3 minutes ===
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

            # === 3. Analyse toutes les secondes si pas de position ===
            if strategy.pm.entry_time is None and latest_candle:
                log_info("🔍 Analyse en cours du marché en temps réel...")
                try:
                    live_price = bingx.get_entry_price(symbol)
                    modified = latest_candle.copy()
                    modified[-1]["close"] = live_price

                    signal = strategy.on_new_candle(modified)

                    if signal and signal.get("side") and signal.get("qty"):
                        log_info(f"🟢 Signal détecté (Score={signal.get('score', 0):.2f}) : {signal}")
                        bingx.place_order_with_protection(
                            symbol=symbol,
                            side=signal["side"],
                            quantity=signal["qty"],
                            tp=signal.get("tp"),
                            sl=signal.get("sl"),
                            trailing_stop=signal.get("trailing_stop"),
                            trailing_offset=signal.get("trailing_offset")
                        )
                except Exception as e:
                    log_error(f"Erreur lors de l’analyse ou de l’exécution : {e}", e)

        except Exception as e:
            log_error(f"💥 Erreur critique dans la boucle principale : {e}", e)
            traceback.print_exc()

        time.sleep(1)

if __name__ == "__main__":
    run_bot()
