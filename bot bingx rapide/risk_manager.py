# risk_manager.py
import datetime
from log_manager import log_info, log_warning, log_error

class RiskManager:
    def __init__(
        self,
        initial_capital: float = 100,
        palier: float = 50,
        progression: float = 8,
        max_qty: float = 9999,
        max_dd_percent: float = 5
    ):
        self.initial_capital = initial_capital
        self.palier = palier
        self.progression = progression
        self.max_qty = max_qty
        self.max_dd = self.initial_capital * (max_dd_percent / 100)

        self.daily_loss = 0.0
        self.last_reset_date = datetime.date.today()

        log_info(f"[RiskManager INIT] Capital initial: {self.initial_capital} | Max Drawdown: {self.max_dd} USDT")

    def calculate_qty(self, equity: float) -> float:
        """
        Calcule la taille de position selon la progression par paliers.
        """
        self._reset_if_new_day()
        palier_count = max(0, int((equity - self.initial_capital) // self.palier))
        qty_raw = 1 + palier_count * (self.progression / 100)
        qty = min(self.max_qty, max(1, qty_raw))
        qty = round(qty, 3)
        log_info(f"[RiskManager] Taille de position calculée: {qty} | Équity: {equity}")
        return qty

    def add_trade_result(self, profit: float):
        """
        Ajoute un résultat de trade. Seules les pertes sont comptées.
        """
        self._reset_if_new_day()
        if profit < 0:
            self.daily_loss += abs(profit)
            log_warning(f"[RiskManager] Perte ajoutée: {abs(profit)} | Perte journalière: {self.daily_loss}")

    def is_blocked(self) -> bool:
        """
        Renvoie True si la perte journalière dépasse le maxDrawdown autorisé.
        """
        self._reset_if_new_day()
        blocked = self.daily_loss > self.max_dd
        if blocked:
            log_error(f"[RiskManager] 🚫 Blocage du trading activé. Perte journalière: {self.daily_loss} > Max autorisé: {self.max_dd}")
        return blocked

    def get_daily_loss(self) -> float:
        return self.daily_loss

    def _reset_if_new_day(self):
        today = datetime.date.today()
        if today != self.last_reset_date:
            log_info("[RiskManager] Nouvelle journée détectée, réinitialisation des pertes.")
            self.daily_loss = 0.0
            self.last_reset_date = today
