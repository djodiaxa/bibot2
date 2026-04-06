import ccxt
import pandas as pd
import pandas_ta as ta
import time
import schedule
import os
import requests

print("🚀 Menyalakan Mesin Cuangine V3 (Mode Detektif Cuan)...")

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

lapor_telegram("🤖 *Bot Cuangine V3 Aktif!*\nSekarang bot bakal lapor pas JUAL juga Bang Hans! 🚀")

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

SYMBOL = 'SOL/USDT:USDT'
TIMEFRAME = '15m'
TRADE_SIZE = 0.1 

# Variabel Ingatan Bot
punya_posisi_sebelumnya = False
menit_ke = 0 

def check_market():
    global punya_posisi_sebelumnya, menit_ke
    try:
        # 1. Ambil Data Market
        bars = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=50)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = ta.rsi(df['close'], length=14)
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        print(f"📊 Market {SYMBOL} | Harga: ${current_price} | RSI: {current_rsi:.2f}")

        # 2. Cek Posisi Sekarang
        posisi_skrg = False
        pnl_skrg = 0
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0:
                posisi_skrg = True
                pnl_skrg = float(pos['info']['unrealisedPnl'])

        # 3. LOGIKA DETEKTIF: JUAL TERDETEKSI
        # Kalau tadi punya posisi, sekarang nggak ada -> Berarti udah laku (TP atau SL kena)
        if punya_posisi_sebelumnya and not posisi_skrg:
            # Ambil riwayat trading terakhir buat tau cuan/rugi pastinya
            history = exchange.fetch_closed_trades(SYMBOL, limit=1)
            if history:
                last_trade = history[0]
                profit = last_trade['info']['closedPnl']
                status_jual = "💰 CUAN GEDE!" if float(profit) > 0 else "💸 CUT LOSS (RUGI)"
                lapor_telegram(f"🚀 *JUAL TERSEKUSI!*\n\nStatus: {status_jual}\nProfit/Loss: `${profit}`\n\nSaldo modal aman, siap berburu lagi! 🔥")
        
        punya_posisi_sebelumnya = posisi_skrg

        # 4. Laporan Rutin (Tiapa 15 Menit)
        if menit_ke % 15 == 0:
            status_pos = "📈 Sedang Jalan" if posisi_skrg else "💤 Menunggu Sinyal"
            info_pnl = f"\nEstimasi PnL: `${pnl_skrg:.4f}`" if posisi_skrg else ""
            lapor_telegram(f"⏱️ *LAPORAN RUTIN*\nHarga {SYMBOL}: `${current_price}`\nRSI: `{current_rsi:.2f}`\nStatus: {status_pos}{info_pnl}")
        
        menit_ke += 1

        # 5. Logika BELI (Hanya jika sedang kosong)
        if current_rsi < 30 and not posisi_skrg:
            lapor_telegram(f"🔥 *SINYAL BELI!* RSI {current_rsi:.2f}\nSikat {SYMBOL}!")
            
            order = exchange.create_market_buy_order(SYMBOL, TRADE_SIZE)
            buy_price = order['average']
            
            lapor_telegram(f"✅ *SUKSES BELI!*\nCoin: {SYMBOL}\nHarga: `${buy_price}`")
            
            # Pasang Jaring TP/SL
            tp = buy_price * 1.05
            sl = buy_price * 0.98
            exchange.create_order(SYMBOL, 'market', 'sell', TRADE_SIZE, params={
                'stopLossPrice': sl, 'takeProfitPrice': tp, 'reduceOnly': True
            })
            lapor_telegram(f"🎯 *JARING DIPASANG!*\nTarget Jual: `${tp:.2f}`\nRem Darurat: `${sl:.2f}`")

    except Exception as e:
        print(f"❌ Error: {e}")

schedule.every(1).minutes.do(check_market)

while True:
    schedule.run_pending()
    time.sleep(1)
                
