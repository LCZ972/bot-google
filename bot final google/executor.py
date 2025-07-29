from my_bingx_api import open_long, open_short, close_all
from position_manager import get_qty
from risk_manager import can_trade, update_daily_loss
from datetime import datetime

current_trade = None  # Suivi du trade actuel

def execute_trade(signal, current_price, config, last_trade_time, side, tp, sl, trail_stop, trail_offset):
    global current_trade

    # Vérifie si on peut encore trader aujourd’hui
    if not can_trade(config, last_trade_time):
        print(f"[{datetime.utcnow().isoformat()}] ⚠️ Trade bloqué par la sécurité journalière.")
        return last_trade_time

    # Calcule la quantité dynamiquement
    try:
        qty = get_qty(config['initial_equity'], config['palier'], config['progression'], config['max_qty'])
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] ❌ Erreur lors du calcul de qty : {e}")
        return last_trade_time

    # Met à jour la perte journalière si nécessaire
    try:
        update_daily_loss(config, current_price, qty, side)
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] ❌ Erreur update_daily_loss : {e}")

    timestamp = datetime.utcnow().isoformat()

    # Exécution du trade
    try:
        if signal == "long":
            open_long(qty, tp, sl, trail_stop, trail_offset)
            print(f"[{timestamp}] ✅ Trade LONG ouvert à {current_price} | Qty: {qty} | TP: {tp} | SL: {sl}")
        elif signal == "short":
            open_short(qty, tp, sl, trail_stop, trail_offset)
            print(f"[{timestamp}] ✅ Trade SHORT ouvert à {current_price} | Qty: {qty} | TP: {tp} | SL: {sl}")
        else:
            print(f"[{timestamp}] ⚠️ Signal inconnu : {signal}")
    except Exception as e:
        print(f"[{timestamp}] ❌ Erreur lors de l'ouverture du trade : {e}")

    return timestamp
