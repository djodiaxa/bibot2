import ccxt
import pandas as pd
import pandas_ta as ta
import time
import schedule
import os
import requests

print("🚀 Menyalakan Mesin Cuangine V2 (Bot Bybit + Telegram)...")

API_KEY = os.environ.get('BYBIT_API_KEY')
API_SECRET = os.environ.get('BYBIT_API_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def lapor_telegram(pesan):
    if TG_TOKEN and TG_CHAT_ID:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"❌ Gagal kirim Telegram: {e}")

lapor_telegram("🤖 *Bot Cuangine V2 Aktif!*\nSiap berburu dolar buat Bang Hans 🚀")

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

SYMBOL = 'SOL/USDT:USDT'
TIMEFRAME = '15m'
TRADE_SIZE = 0.1 

# Penghitung waktu untuk laporan rutin
menit_ke = 0 

def check_buy_condition():
    global menit_ke
    try:
        # 1. Cek Harga & RSI
        bars = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=50)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = ta.rsi(df['close'], length=14)
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        log_pantau = f"📊 Market {SYMBOL} | Harga: ${current_price} | RSI: {current_rsi:.2f}"
        print(log_pantau)

        # 2. Cek apakah ada posisi yang sedang jalan (Profit / Loss)
        posisi_terbuka = ""
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0:
                pnl = float(pos['info']['unrealisedPnl'])
                status_pnl = "🟢 CUAN" if pnl > 0 else "🔴 MINUS"
                posisi_terbuka = f"\n\n📈 *Posisi Aktif:*\nUkuran: {pos['contracts']} SOL\nUnrealized PnL: {status_pnl} ${pnl:.4f}"

        # 3. Laporan Rutin Telegram (Setiap 15 Menit agar tidak spam)
        if menit_ke % 15 == 0:
            lapor_telegram(f"⏱️ *UPDATE PASAR (15 Menit)*\n{log_pantau}{posisi_terbuka}")
        menit_ke += 1

        # 4. Sinyal Eksekusi Beli (Hanya jika belum punya posisi)
        if current_rsi < 30 and posisi_terbuka == "":
            pesan_sinyal = f"🔥 *SINYAL BUY!* RSI jatuh ke {current_rsi:.2f}\nSikat miring {SYMBOL}..."
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
            
            lapor_telegram(f"🎯 *Jaring Dipasang!*\n💰 Take Profit: ${take_profit_price:.2f}\n🛡 Stop Loss: ${stop_loss_price:.2f}")
            
    except Exception as e:
        print(f"❌ ERROR BOT: {e}")

# Jalankan rutin
schedule.every(1).minutes.do(check_buy_condition)

while True:
    schedule.run_pending()
    time.sleep(1)
    
