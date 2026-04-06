import ccxt
import pandas as pd
import pandas_ta as ta
import time
import schedule
import os
import requests

print("🚀 Menyalakan Mesin Cuangine (Bot Bybit + Telegram)...")

# Mengambil Kunci dari Railway
API_KEY = os.environ.get('BYBIT_API_KEY')
API_SECRET = os.environ.get('BYBIT_API_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Fungsi untuk ngirim pesan ke Telegram Abang
def lapor_telegram(pesan):
    if TG_TOKEN and TG_CHAT_ID:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"❌ Gagal kirim Telegram: {e}")

lapor_telegram("🤖 *Bot Trading Aktif!*\nSiap memantau market SOL/USDT 24/7 buat Abang 🚀")

# Inisialisasi Bybit
exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

SYMBOL = 'SOL/USDT:USDT'
TIMEFRAME = '15m'
TRADE_SIZE = 0.1 

def check_buy_condition():
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=50)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df['rsi'] = ta.rsi(df['close'], length=14)
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        print(f"📊 Market {SYMBOL} | Harga: ${current_price} | RSI: {current_rsi:.2f}")

        # Sinyal Buy jika RSI < 30
        if current_rsi < 30:
            pesan_sinyal = f"🔥 *SINYAL BUY!* RSI jatuh ke {current_rsi:.2f}\nMengeksekusi pembelian {SYMBOL}..."
            print(pesan_sinyal)
            lapor_telegram(pesan_sinyal)
            
            # Eksekusi Beli
            order = exchange.create_market_buy_order(SYMBOL, TRADE_SIZE)
            buy_price = order['average']
            
            pesan_sukses = f"✅ *SUKSES BELI!*\nCoin: {SYMBOL}\nJumlah: {TRADE_SIZE}\nHarga: ${buy_price}"
            print(pesan_sukses)
            lapor_telegram(pesan_sukses)
            
            # Pasang Take Profit (5%) & Stop Loss (2%)
            take_profit_price = buy_price * 1.05
            stop_loss_price = buy_price * 0.98
            
            exchange.create_order(SYMBOL, 'market', 'sell', TRADE_SIZE, params={
                'stopLossPrice': stop_loss_price,
                'takeProfitPrice': take_profit_price,
                'reduceOnly': True
            })
            
            pesan_jaring = f"🎯 *Jaring Dipasang!*\n💰 Take Profit: ${take_profit_price:.2f}\n🛡 Stop Loss: ${stop_loss_price:.2f}"
            print(pesan_jaring)
            lapor_telegram(pesan_jaring)
            
            # Tidur sejam biar nggak dobel beli
            time.sleep(3600) 
            
    except Exception as e:
        error_msg = f"❌ *ERROR BOT:*\n{e}"
        print(error_msg)
        lapor_telegram(error_msg)

# Jadwal cek setiap 1 menit
schedule.every(1).minutes.do(check_buy_condition)

while True:
    schedule.run_pending()
    time.sleep(1)
    
