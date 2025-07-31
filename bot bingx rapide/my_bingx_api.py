import requests
import time
from log_manager import log_info, log_error

class BingxAPI:
    def __init__(self, api_key, api_secret, timestamp="local"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.timestamp = timestamp

    def open_market_order(self, symbol, side, quantity, tp=None, sl=None, trailing_stop=None, position_side=None):
        """
        Envoie un ordre de marché à BingX avec gestion de TP/SL/Trailing Stop
        """
        try:
            order_data = {
                "symbol": symbol,
                "side": side.upper(),  # 'BUY' ou 'SELL'
                "positionSide": position_side or ("LONG" if side.upper() == "BUY" else "SHORT"),
                "type": "MARKET",
                "quantity": quantity,
            }

            if tp:
                order_data["takeProfit"] = {
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": tp,
                    "price": tp,
                    "workingType": "MARK_PRICE"
                }

            if sl:
                order_data["stopLoss"] = {
                    "type": "STOP_MARKET",
                    "stopPrice": sl,
                    "price": sl,
                    "workingType": "MARK_PRICE"
                }

            if trailing_stop:
                order_data["trailingStop"] = {
                    "callbackRate": trailing_stop,
                    "workingType": "MARK_PRICE"
                }

            log_info(f"📤 Envoi d’un ordre BingX : {order_data}")

            # TODO: appel réel à l’API BingX ici
            response = {
                "success": True,
                "order": order_data
            }

            if not response.get("success"):
                error_msg = response.get("message", "Erreur inconnue BingX")
                if "insufficient balance" in error_msg.lower():
                    raise ValueError("❌ Solde insuffisant pour l’ordre.")
                if "quantity" in error_msg.lower():
                    raise ValueError("❌ Taille d’ordre invalide.")
                raise ValueError(f"BingX Error : {error_msg}")

            log_info("✅ Ordre placé avec succès.")
            return response["order"]

        except Exception as e:
            log_error(f"[ERREUR] open_market_order : {e}")
            return None

    def place_trailing_stop_order(self, symbol, side, quantity, trail_value):
        try:
            data = {
                "symbol": symbol,
                "side": side.upper(),
                "qty": quantity,
                "trail_value": trail_value
            }
            log_info(f"[TRAILING] 📤 Envoi trailing stop : {data}")
            return data
        except Exception as e:
            log_error(f"[ERREUR] place_trailing_stop_order : {e}")
            return None

    def get_my_perpetual_swap_positions(self, symbol):
        try:
            data = {"symbol": symbol, "positions": []}
            log_info(f"[POSITIONS] 📄 Chargées pour {symbol} : {data}")
            return data
        except Exception as e:
            log_error(f"[ERREUR] get_my_perpetual_swap_positions : {e}")
            return None

    def get_perpetual_balance(self):
        try:
            balance = {"balance": 1000.0}
            log_info(f"[BALANCE] 💰 Solde actuel : {balance}")
            return balance
        except Exception as e:
            log_error(f"[ERREUR] get_perpetual_balance : {e}")
            return None
        
    def modify_stop_loss(self, symbol, new_sl_price, position_side):
        try:
            data = {
                "symbol": symbol,
                "stopPrice": new_sl_price,
                "positionSide": position_side.upper(),  # 'LONG' ou 'SHORT'
                "workingType": "MARK_PRICE"
            }
            log_info(f"[STOP-LOSS] 🔧 Modification du stop-loss : {data}")
        
            # TODO : Remplacer par un vrai appel API vers BingX pour modifier le SL
            response = {
                "success": True,
                "data": data
            }

            if not response.get("success"):
                raise ValueError(f"BingX Error : {response.get('message', 'Erreur inconnue')}")

            log_info("✅ Stop-loss modifié avec succès.")
            return response["data"]
    
        except Exception as e:
            log_error(f"[ERREUR] modify_stop_loss : {e}")
            return None


class BingxClient:
    def __init__(self, api_key, api_secret):
        self.client = BingxAPI(api_key, api_secret, timestamp="local")

    def open_market_order(self, symbol, side, quantity, tp=None, sl=None, trailing_stop=None, position_side=None):
        return self.client.open_market_order(
            symbol, side, quantity, tp=tp, sl=sl, trailing_stop=trailing_stop, position_side=position_side
        )

    def close_market_order(self, symbol, side):
        close_side = "SELL" if side.upper() == "BUY" else "BUY"
        log_info(f"[FERMETURE] 🔒 Fermeture position : {symbol} {close_side}")
        return self.client.open_market_order(symbol, close_side, quantity=0.01)

    def place_trailing(self, symbol, side, quantity, trail_value):
        return self.client.place_trailing_stop_order(symbol, side.upper(), quantity, trail_value)

    def get_positions(self, symbol):
        return self.client.get_my_perpetual_swap_positions(symbol)

    def get_balance(self):
        return self.client.get_perpetual_balance()
    
    def modify_stop_loss(self, symbol, new_sl_price, position_side):
        return self.client.modify_stop_loss(symbol, new_sl_price, position_side)


from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("BINGX_API_KEY")
api_secret = os.getenv("BINGX_API_SECRET")

def get_wallet_balance():
    try:
        client = BingxClient(api_key=api_key, api_secret=api_secret)
        balance_data = client.get_balance()
        if balance_data and "balance" in balance_data:
            return float(balance_data["balance"])
        else:
            log_error("[bingx_client] ❌ Clé 'balance' manquante dans la réponse.")
            return None
    except Exception as e:
        log_error(f"[bingx_client] Erreur récupération solde : {e}")
        return None