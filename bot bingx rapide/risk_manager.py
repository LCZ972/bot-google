# risk_manager.py
import datetime
from log_manager import log_info, log_warning, log_error

class RiskManager:
    def __init__(
        self,
        bingx_client,
        initial_capital: float = 100,
        palier: float = 50,
        progression: float = 8,
        max_qty: float = 9999,
        max_dd_percent: float = 5
    ):
        self.bingx_client = bingx_client
        self.initial_capital = initial_capital
        self.palier = palier
        self.progression = progression
        self.max_qty = max_qty
        self.max_dd_percent = max_dd_percent

        self.daily_loss = 0.0
        self.last_reset_date = datetime.date.today()
        self.starting_balance = self._initialize_starting_balance()

        log_info(f"[RiskManager INIT] Solde initial jour: {self.starting_balance} USDT | Max DD%: {self.max_dd_percent}%")

    def calculate_qty(self, equity: float) -> float:
        self._reset_if_new_day()
        palier_count = max(0, int((equity - self.initial_capital) // self.palier))
        qty_raw = 1 + palier_count * (self.progression / 100)
        qty = min(self.max_qty, max(1, qty_raw))
        qty = round(qty, 3)
        log_info(f"[RiskManager] Taille de position calculée: {qty} | Équity: {equity}")
        return qty

    def add_trade_result(self, profit: float):
        self._reset_if_new_day()
        if profit < 0:
            self.daily_loss += abs(profit)
            log_warning(f"[RiskManager] ➖ Perte ajoutée: {abs(profit)} | Perte journalière brute: {self.daily_loss}")

    def is_blocked(self) -> bool:
        self._reset_if_new_day()

        balance_data = self.bingx_client.get_balance()
        if balance_data is None or "balance" not in balance_data:
            log_error("[RiskManager] ❌ Solde introuvable. Impossibilité d’évaluer le blocage.")
            return False

        current_balance = float(balance_data["balance"])
        drawdown = self.starting_balance - current_balance
        max_allowed = self.starting_balance * (self.max_dd_percent / 100)

        if drawdown > max_allowed:
            log_error(f"[RiskManager] 🚫 Drawdown dépassé ! {drawdown:.2f} > {max_allowed:.2f}")
            return True
        else:
            log_info(f"[RiskManager] ✅ Drawdown OK : {drawdown:.2f} / {max_allowed:.2f}")
            return False

    def get_daily_loss(self) -> float:
        return self.daily_loss

    def _reset_if_new_day(self):
        today = datetime.date.today()
        if today != self.last_reset_date:
            log_info("[RiskManager] 🌅 Nouvelle journée, reset des pertes et du solde initial.")
            self.daily_loss = 0.0
            self.last_reset_date = today
            self.starting_balance = self._initialize_starting_balance()

    def _initialize_starting_balance(self) -> float:
        balance_data = self.bingx_client.get_balance()
        if balance_data is None or "balance" not in balance_data:
            log_warning("[RiskManager] ❗ Fallback sur capital initial (solde introuvable).")
            return self.initial_capital
        return float(balance_data["balance"])
