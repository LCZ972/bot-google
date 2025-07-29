# indicators.py
import pandas as pd

class Indicators:
    def ema(self, series, period):
        if len(series) < period:
            print(f"[EMA] Not enough data for period {period}. Received {len(series)} elements.")
            return [0] * len(series)
        result = pd.Series(series).ewm(span=period, adjust=False).mean().tolist()
        print(f"[EMA] Calculated EMA({period}) for {len(series)} points.")
        return result

    def sma(self, series, period):
        if len(series) < period:
            print(f"[SMA] Not enough data for period {period}. Received {len(series)} elements.")
            return [0] * len(series)
        result = pd.Series(series).rolling(window=period).mean().tolist()
        print(f"[SMA] Calculated SMA({period}) for {len(series)} points.")
        return result

    def rsi(self, series, period=14):
        if len(series) < period:
            print(f"[RSI] Not enough data for RSI({period}). Received {len(series)} elements.")
            return [0] * len(series)
        delta = pd.Series(series).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        result = rsi.fillna(0).tolist()
        print(f"[RSI] Calculated RSI({period}) for {len(series)} points.")
        return result

    def atr(self, high, low, close, period=14):
        if min(len(high), len(low), len(close)) < period:
            print(f"[ATR] Not enough data for ATR({period}).")
            return [0] * len(close)
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        result = atr.fillna(0).tolist()
        print(f"[ATR] Calculated ATR({period}) for {len(close)} points.")
        return result
