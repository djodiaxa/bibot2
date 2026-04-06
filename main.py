import ccxt
import pandas as pd
import pandas_ta as ta
import time
import schedule
import os

print("🚀 Menyalakan Mesin Cuangine (Bot Bybit Futures)...")

# Mengambil API Key dari tab Variables di Railway
API_KEY = os.environ.get('BYBIT_API_KEY')
API_SECRET = os.environ.get('BYBIT_API_SECRET')

# Inisialisasi Bybit lewat CCXT
exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'linear' # Wajib 'linear' untuk Futures/Derivatives USDT
    }
})

SYMBOL = 'SOL/USDT:USDT'
TIMEFRAME = '15m' # Cek grafik per 15 menit
TRADE_SIZE = 0.1 # Jumlah SOL yang dibeli (sesuaikan dengan modal $10 pakai leverage)

def check_buy_condition():
    try:
        # 1. Ambil data grafik OHLCV
        bars = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=50)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 2. Hitung indikator RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        print(f"📊 Cek Market {SYMBOL} | Harga: ${current_price} | RSI: {current_rsi:.2f}")

        # 3. Logika "Yang Cuan Aja": Beli pas lagi diskon/oversold (RSI < 30)
        if current_rsi < 30:
            print(f"🔥 SINYAL BUY MUNCUL! RSI di bawah 30 ({current_rsi:.2f}). Mengeksekusi Order...")
            
            # Buka Posisi Long (Beli)
            order = exchange.create_market_buy_order(SYMBOL, TRADE_SIZE)
            buy_price = order['average']
            print(f"✅ SUKSES MEMBELI {TRADE_SIZE} {SYMBOL} di harga ${buy_price}")
            
            # Pasang Jaring Jaring Keamanan (Take Profit & Stop Loss)
            # Take profit saat harga naik 5%, Stop Loss kalau harga turun 2%
            take_profit_price = buy_price * 1.05
            stop_loss_price = buy_price * 0.98
            
            # Kirim perintah Take Profit ke Bybit
            exchange.create_order(SYMBOL, 'market', 'sell', TRADE_SIZE, params={
                'stopLossPrice': stop_loss_price,
                'takeProfitPrice': take_profit_price,
                'reduceOnly': True
            })
            print(f"🎯 Jaring otomatis dipasang! TP: ${take_profit_price:.2f} | SL: ${stop_loss_price:.2f}")
            
            # Tidurkan bot sebentar biar nggak dobel beli
            time.sleep(3600) 
            
    except Exception as e:
        print(f"❌ Terjadi Error: {e}")

# Jalankan pengecekan setiap 1 menit
schedule.every(1).minutes.do(check_buy_condition)

print("✅ Bot Aktif dan sedang memantau market 24/7...")
while True:
    schedule.run_pending()
    time.sleep(1)
