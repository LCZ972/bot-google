# memory.py
import json
import os
from collections import deque
from log_manager import log_event

MEMORY_FILE = "recent_trades.json"

class TradeMemory:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.recent_profits = deque(maxlen=max_size)
        self._load_from_file()
        log_event("[🧠 MEMORY] Initialisée avec capacité max : {} trades.", self.max_size)

    def add_trade(self, profit: float):
        self.recent_profits.append(profit)
        self._save_to_file()
        log_event("[🧠 MEMORY] Nouveau trade ajouté : {:.2f} USDT | Total mémorisé : {}", profit, len(self.recent_profits))

    def get_average_profit(self):
        if not self.recent_profits:
            log_event("[🧠 MEMORY] Aucune donnée pour le calcul du profit moyen.")
            return 0.0
        avg = sum(self.recent_profits) / len(self.recent_profits)
        log_event("[🧠 MEMORY] Profit moyen calculé : {:.2f} USDT", avg)
        return avg

    def get_last_trades(self):
        trades = list(self.recent_profits)
        log_event("[🧠 MEMORY] Historique des derniers trades : {}", trades)
        return trades

    def _save_to_file(self):
        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(list(self.recent_profits), f)
            log_event("[💾 MEMORY] Données enregistrées dans '{}'.", MEMORY_FILE)
        except Exception as e:
            log_event("[❌ MEMORY] Échec de sauvegarde dans '{}'. Erreur : {}", MEMORY_FILE, str(e))

    def _load_from_file(self):
        if not os.path.exists(MEMORY_FILE):
            log_event("[📂 MEMORY] Aucun fichier existant '{}' trouvé. Initialisation vide.", MEMORY_FILE)
            return
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                for profit in data[-self.max_size:]:
                    self.recent_profits.append(profit)
            log_event("[📥 MEMORY] {} trades chargés depuis '{}'.", len(self.recent_profits), MEMORY_FILE)
        except Exception as e:
            log_event("[❌ MEMORY] Erreur lors du chargement de '{}'. Erreur : {}", MEMORY_FILE, str(e))
