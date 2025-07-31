
import ccxt
import time

def fetch_ohlcv(symbol='BTC/USDT', timeframe='3m', limit=100):
    exchange = ccxt.binance()  # Utilisation de Binance car BingX ne supporte pas ccxt complet
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return bars

def get_latest_candle(bars):
    return bars[-1] if bars else None
