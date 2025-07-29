# memory.py
from collections import deque
import logging

class TradeMemory:
    def __init__(self, max_size=10):
        self.recent_profits = deque(maxlen=max_size)
        logging.info(f"[🧠 MEMORY] Initialisée avec capacité max : {max_size} trades.")

    def add_trade(self, profit: float):
        self.recent_profits.append(profit)
        logging.info(f"[🧠 MEMORY] Nouveau trade ajouté : {profit} USDT | Total mémorisé : {len(self.recent_profits)}")

    def get_average_profit(self):
        if not self.recent_profits:
            logging.info("[🧠 MEMORY] Aucune donnée pour le calcul du profit moyen.")
            return 0.0
        avg = sum(self.recent_profits) / len(self.recent_profits)
        logging.info(f"[🧠 MEMORY] Profit moyen calculé : {avg:.2f} USDT")
        return avg

    def get_last_trades(self):
        logging.info(f"[🧠 MEMORY] Historique des derniers trades : {list(self.recent_profits)}")
        return list(self.recent_profits)
