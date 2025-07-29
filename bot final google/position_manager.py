# position_manager.py
import time
from my_bingx_api import BingxClient

class PositionManager:
    def __init__(self, api_key, api_secret, symbol="BTC-USDT"):
        self.api = BingxClient(api_key, api_secret)
        self.last_trade_time = 0
        self.entry_time = None
        self.symbol = symbol

    def can_trade(self, cooldown_min):
        now = time.time()
        cooldown_passed = (now - self.last_trade_time) > cooldown_min * 60
        print(f"[COOLDOWN] Last trade: {self.last_trade_time:.0f}, Now: {now:.0f}, Passed: {cooldown_passed}")
        return cooldown_passed

    def open_trade(self, side: str, qty: float, tp: float = None, sl: float = None):
        try:
            print(f"[TRADE] Tentative ouverture de position: side={side}, qty={qty}, TP={tp}, SL={sl}")
            response = self.api.open_market_order(
                symbol=self.symbol,
                side=side,
                quantity=qty,
                tp=tp,
                sl=sl
            )
            if response.get("success", False):
                self.entry_time = time.time()
                self.last_trade_time = time.time()
                print(f"[✅ OUVERTURE] Trade ouvert avec succès ({side})")
                return True
            else:
                print(f"[❌ ERREUR OUVERTURE] Réponse API: {response}")
                return False
        except Exception as e:
            print(f"[❌ EXCEPTION OUVERTURE] {e}")
            return False

    def close_trade(self, side: str):
        try:
            print(f"[FERMETURE] Fermeture de la position en {side}")
            result = self.api.close_market_order(symbol=self.symbol, side=side)
            print(f"[✅ FERMETURE] Réponse API : {result}")
            return result
        except Exception as e:
            print(f"[❌ EXCEPTION FERMETURE] {e}")
            return None

    def set_trailing(self, side: str, qty: float, trail_value: float):
        try:
            print(f"[TRAILING] Déclenchement trailing stop : side={side}, qty={qty}, valeur={trail_value}")
            return self.api.place_trailing(self.symbol, side, qty, trail_value)
        except Exception as e:
            print(f"[❌ EXCEPTION TRAILING] {e}")
            return None

    def trade_duration_minutes(self):
        if not self.entry_time:
            return 0
        return (time.time() - self.entry_time) / 60

    def check_exit_conditions(self, entry_price, tp, sl, side):
        try:
            current_price = self.api.get_price(self.symbol)
            if not current_price:
                print("[❌ PRIX] Impossible d’obtenir le prix actuel.")
                return None

            print(f"[SURVEILLANCE] Prix actuel: {current_price}, TP: {tp}, SL: {sl}, Side: {side}")

            if side == "BUY":
                if current_price >= tp:
                    print("🎯 TP atteint (LONG) → fermeture")
                    self.close_trade("BUY")
                    print("[ℹ️ FERMETURE CONFIRMÉE] Position LONG fermée à TP.")
                    return "tp"
                elif current_price <= sl:
                    print("🛑 SL atteint (LONG) → fermeture")
                    self.close_trade("BUY")
                    print("[ℹ️ FERMETURE CONFIRMÉE] Position LONG fermée à SL.")
                    return "sl"

            elif side == "SELL":
                if current_price <= tp:
                    print("🎯 TP atteint (SHORT) → fermeture")
                    self.close_trade("SELL")
                    print("[ℹ️ FERMETURE CONFIRMÉE] Position SHORT fermée à TP.")
                    return "tp"
                elif current_price >= sl:
                    print("🛑 SL atteint (SHORT) → fermeture")
                    self.close_trade("SELL")
                    print("[ℹ️ FERMETURE CONFIRMÉE] Position SHORT fermée à SL.")
                    return "sl"

        except Exception as e:
            print(f"[❌ EXCEPTION SURVEILLANCE] {e}")
        return None
