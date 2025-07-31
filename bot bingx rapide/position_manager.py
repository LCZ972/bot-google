# position_manager.py

import time
from my_bingx_api import BingxClient
from log_manager import log_event
from memory import save_recent_win
from log_trades import log_profit

class PositionManager:
    def __init__(self, api_key, api_secret, symbol="BTC-USDT"):
        self.api = BingxClient(api_key, api_secret)
        self.last_trade_time = 0
        self.entry_time = None
        self.entry_price = None
        self.symbol = symbol

    def can_trade(self, cooldown_min):
        now = time.time()
        cooldown_passed = (now - self.last_trade_time) > cooldown_min * 60
        log_event("cooldown_check", {
            "last_trade_time": self.last_trade_time,
            "now": now,
            "cooldown_passed": cooldown_passed
        })
        return cooldown_passed

    def open_trade(self, side: str, qty: float, tp: float = None, sl: float = None):
        try:
            log_event("open_trade_attempt", {"side": side, "qty": qty, "tp": tp, "sl": sl})
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
                self.entry_price = self.api.get_price(self.symbol)
                log_event("trade_opened", {"side": side, "entry_price": self.entry_price, "response": response})
                return True
            else:
                log_event("trade_open_error", {"response": response})
                return False
        except Exception as e:
            log_event("exception_open_trade", {"error": str(e)})
            return False

    def close_trade(self, side: str):
        try:
            log_event("close_trade_attempt", {"side": side})
            result = self.api.close_market_order(symbol=self.symbol, side=side)
            log_event("trade_closed", {"side": side, "result": result})

            close_price = self.api.get_price(self.symbol)
            if self.entry_price and close_price:
                if side == "BUY":
                    profit = close_price - self.entry_price
                else:
                    profit = self.entry_price - close_price
                save_recent_win(profit)
                log_event("profit_saved", {"profit": profit})

            return result
        except Exception as e:
            log_event("exception_close_trade", {"error": str(e)})
            return None

    def set_trailing(self, side: str, qty: float, trail_value: float):
        try:
            log_event("trailing_set_attempt", {"side": side, "qty": qty, "trail_value": trail_value})
            return self.api.place_trailing(self.symbol, side, qty, trail_value)
        except Exception as e:
            log_event("exception_trailing", {"error": str(e)})
            return None

    def trade_duration_minutes(self):
        if not self.entry_time:
            return 0
        duration = (time.time() - self.entry_time) / 60
        log_event("trade_duration", {"minutes": duration})
        return duration

    def check_exit_conditions(self, entry_price, tp, sl, side, qty):  # ✅ qty ajouté
        try:
            current_price = self.api.get_price(self.symbol)
            if not current_price:
                log_event("price_fetch_failed", {"symbol": self.symbol})
                return None

            log_event("monitor_price", {
                "symbol": self.symbol,
                "current_price": current_price,
                "tp": tp,
                "sl": sl,
                "side": side
            })

            if side == "BUY":
                if current_price >= tp:
                    self.close_trade("BUY")
                    log_event("tp_hit", {"side": "BUY", "price": current_price})
                    pnl = (current_price - entry_price) * qty
                    log_profit(pnl)
                    return "tp"
                elif current_price <= sl:
                    self.close_trade("BUY")
                    log_event("sl_hit", {"side": "BUY", "price": current_price})
                    pnl = (current_price - entry_price) * qty
                    log_profit(pnl)
                    return "sl"

            elif side == "SELL":
                if current_price <= tp:
                    self.close_trade("SELL")
                    log_event("tp_hit", {"side": "SELL", "price": current_price})
                    pnl = (entry_price - current_price) * qty
                    log_profit(pnl)
                    return "tp"
                elif current_price >= sl:
                    self.close_trade("SELL")
                    log_event("sl_hit", {"side": "SELL", "price": current_price})
                    pnl = (entry_price - current_price) * qty
                    log_profit(pnl)
                    return "sl"

        except Exception as e:
            log_event("exception_check_exit", {"error": str(e)})
        return None
