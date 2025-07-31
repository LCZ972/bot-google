import os
import json

TRADES_LOG_FILE = "recent_trades.json"  

def get_adjust_factor():
    try:
        if not os.path.exists(TRADES_LOG_FILE):
            return 1.0

        with open(TRADES_LOG_FILE, "r") as file:
            trades = json.load(file)

        if not trades:
            return 1.0

        trades = trades[-10:]
        pnls = [float(t["pnl"]) for t in trades if "pnl" in t]

        if not pnls:
            return 1.0

        avg_pnl = sum(pnls) / len(pnls)

        if avg_pnl >= 15:
            return 1.3
        elif avg_pnl >= 5:
            return 1.1
        elif avg_pnl >= 0:
            return 1.0
        else:
            return 0.7

    except Exception as e:
        print(f"[AI_MODULE] Erreur adjust_factor: {e}")
        return 1.0