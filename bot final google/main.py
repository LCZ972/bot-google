# main.py
import time
import traceback
from strategy import SmartEntryStrategy
from my_bingx_api import BingxClient
from indicators import Indicators
from config import config
from data_feed import fetch_ohlcv

# === CONFIGURATION API ===
API_KEY = "TON_API_KEY"
API_SECRET = "TON_API_SECRET"

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
    print("🚀 [INFO] Bot lancé avec surveillance live chaque seconde (sans Supabase)")

    while True:
        try:
            now = time.time()

            # === 1. Vérifie TP / SL en live si une position est ouverte ===
            if strategy.pm.entry_time is not None:
                print("🔄 [TRADE] Vérification TP/SL en cours...")
                try:
                    entry_price = bingx.get_entry_price(symbol)
                    strategy.pm.check_exit_conditions(
                        entry_price=entry_price,
                        tp=strategy.pm.tp_target,
                        sl=strategy.pm.sl_target,
                        side=strategy.pm.current_side
                    )
                except Exception as e:
                    print(f"❌ [ERROR] Erreur vérification TP/SL : {e}")

            # === 2. Rafraîchissement des bougies toutes les 3 min ===
            if now - last_m3_refresh > M3_INTERVAL:
                print("📡 [MARCHÉ] Récupération bougies (M3)...")
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
                    print("✅ [DATA] Bougies M3 mises à jour")
                else:
                    print("⚠️ [WARN] Impossible de récupérer les bougies")

            # === 3. Analyse toutes les secondes si pas de position ===
            if strategy.pm.entry_time is None and latest_candle:
                print("🔍 [SCAN] Recherche opportunité avec prix actuel...")
                try:
                    live_price = bingx.get_entry_price(symbol)
                    modified = latest_candle.copy()
                    modified[-1]["close"] = live_price  # Met à jour le close en live

                    strategy.on_new_candle(modified)
                except Exception as e:
                    print(f"❌ [ERROR] Erreur analyse en live : {e}")

        except Exception as e:
            print(f"💥 [CRASH] Erreur dans la boucle principale : {e}")
            traceback.print_exc()

        time.sleep(1)

if __name__ == "__main__":
    run_bot()