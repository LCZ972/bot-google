# log_trades.py
import json
import os

TRADES_LOG_FILE = "recent_trades.json"

def log_profit(pnl):
    try:
        if os.path.exists(TRADES_LOG_FILE):
            with open(TRADES_LOG_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = []

        data.append({"pnl": pnl})
        with open(TRADES_LOG_FILE, 'w') as f:
            json.dump(data[-10:], f)
        print(f"[LOG] PnL enregistré : {pnl}")

    except Exception as e:
        print(f"[LOG] Erreur enregistrement PnL : {e}")
