# strategy.py

import time
from indicators import Indicators
from memory import TradeMemory
from risk_manager import RiskManager
from position_manager import PositionManager
from my_bingx_api import BingxClient


class SmartEntryStrategy:
    def __init__(self, api_key, api_secret):
        self.symbol = "BTC-USDT"
        self.atr_period = 14
        self.tp_multiplier = 2.2
        self.sl_multiplier = 1.3
        self.trail_multiplier = 0.9
        self.offset_multiplier = 0.6
        self.cooldown_min = 20
        self.last_trade_time = 0

        self.indicators = Indicators()
        self.memory = TradeMemory(10)
        self.risk = RiskManager(initial_capital=100, palier=50, progression=8, max_qty=9999, max_dd_percent=5)
        self.api = BingxClient(api_key, api_secret)
        self.pm = PositionManager(api_key, api_secret, symbol=self.symbol)

    def on_new_candle(self, candles):
        now = time.time()
        if now - self.last_trade_time < self.cooldown_min * 60:
            return

        try:
            close = [c["close"] for c in candles]
            high = [c["high"] for c in candles]
            low = [c["low"] for c in candles]
            volume = [c["volume"] for c in candles]

            ema21 = self.indicators.ema(close, 21)
            ema50 = self.indicators.ema(close, 50)
            ema200 = self.indicators.ema(close, 200)
            rsi = self.indicators.rsi(close, 14)
            atr = self.indicators.atr(high, low, close, self.atr_period)
            atr_avg = self.indicators.sma(atr, 100)
            volume_avg = self.indicators.sma(volume, 20)
        except Exception as e:
            print(f"❌ Erreur indicateurs techniques : {e}")
            return

        bull_break = close[-1] > max(close[-9:-1]) and close[-1] > ema21[-1] and rsi[-1] > 55
        bear_break = close[-1] < min(close[-9:-1]) and close[-1] < ema21[-1] and rsi[-1] < 45
        volume_ok = volume[-1] > volume_avg[-1] * 0.8
        volatility_ok = atr[-1] > atr_avg[-1] * 1.1
        trend_up = ema21[-1] > ema50[-1] > ema200[-1]
        trend_down = ema21[-1] < ema50[-1] < ema200[-1]

        long_cond = bull_break and volume_ok and volatility_ok and trend_up
        short_cond = bear_break and volume_ok and volatility_ok and trend_down

        if self.risk.is_blocked():
            print("⛔ Blocage journalier activé : perte max atteinte.")
            return

        balance_info = self.api.get_balance()
        equity = float(balance_info["equity"])
        qty = self.risk.calculate_qty(equity)

        avg_recent_win = self.memory.get_average_profit()
        adjust_factor = 1.2 if avg_recent_win > 0 else 0.7
        tp_adj = atr[-1] * self.tp_multiplier * adjust_factor
        sl_adj = atr[-1] * self.sl_multiplier / adjust_factor
        trail_stop = atr[-1] * self.trail_multiplier
        trail_offset = atr[-1] * self.offset_multiplier

        if long_cond and self.pm.can_trade(self.cooldown_min):
            print("📈 Signal LONG détecté")
            if self.pm.open_trade("BUY", qty, tp_adj, sl_adj):
                print(f"✅ Position LONG ouverte @ {close[-1]} | TP: {tp_adj:.2f} | SL: {sl_adj:.2f}")
                self.pm.set_trailing("BUY", qty, trail_stop - trail_offset)
                self.pm.tp_target = close[-1] + tp_adj
                self.pm.sl_target = close[-1] - sl_adj
                self.pm.current_side = "BUY"
                self.pm.entry_price = close[-1]
                self.last_trade_time = now

        elif short_cond and self.pm.can_trade(self.cooldown_min):
            print("📉 Signal SHORT détecté")
            if self.pm.open_trade("SELL", qty, tp_adj, sl_adj):
                print(f"✅ Position SHORT ouverte @ {close[-1]} | TP: {tp_adj:.2f} | SL: {sl_adj:.2f}")
                self.pm.set_trailing("SELL", qty, trail_stop - trail_offset)
                self.pm.tp_target = close[-1] - tp_adj
                self.pm.sl_target = close[-1] + sl_adj
                self.pm.current_side = "SELL"
                self.pm.entry_price = close[-1]
                self.last_trade_time = now
