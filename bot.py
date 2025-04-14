import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import threading
import schedule
import time
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from io import BytesIO

TOKEN = '7582918522:AAEsqowrP7ftba8nW6TbGgjdQ3Eivrzg7Cs'
CMC_API_KEY = 'bd5f81f5-9e2c-4483-8060-ff7eb41b3a54'
USER_ID = 2036758982
bot = telebot.TeleBot(TOKEN)
TOKENS = ["SOL", "JUP", "BONK", "PYTH"]
TRADE_AMOUNT = 10  # 💸 Каждая сделка на $10
TRADES_FILE = 'trades.json'

# Загружаем историю сделок
if os.path.exists(TRADES_FILE):
    with open(TRADES_FILE, 'r') as f:
        trades = json.load(f)
else:
    trades = []

def save_trades():
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)

def get_token_price(symbol):
    try:
        url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
        params = {'symbol': symbol, 'convert': 'USD'}
        res = requests.get(url, headers=headers, params=params).json()
        price = res["data"][symbol]["quote"]["USD"]["price"]
        return round(price, 6)
    except Exception as e:
        print(f"Ошибка цены {symbol}: {e}")
        return "н/д"

def get_historical_prices(symbol="SOL"):
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=48, freq="30min")
    prices = [100 + (i % 5) + (i / 20.0) for i in range(48)]
    df = pd.DataFrame({"timestamp": timestamps, "price": prices})
    df.set_index("timestamp", inplace=True)
    return df

def calculate_indicators(df):
    df["MA10"] = df["price"].rolling(window=10).mean()
    delta = df["price"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def build_chart(symbol):
    try:
        df = get_historical_prices(symbol)
        df = calculate_indicators(df)
        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df["price"], label="Цена")
        plt.plot(df.index, df["MA10"], label="MA10", linestyle="--")
        plt.title(f"{symbol} - Цена и MA10")
        plt.xlabel("Время")
        plt.ylabel("USD")
        plt.legend()
        plt.grid()
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        return buffer
    except Exception as e:
        print("Ошибка графика:", e)
        return None

def ai_signal(symbol):
    try:
        df = get_historical_prices(symbol)
        df = calculate_indicators(df)
        rsi = df["RSI"].iloc[-1]
        ma = df["MA10"].iloc[-1]
        price = df["price"].iloc[-1]
        msg = f"📊 {symbol}:\nЦена: ${round(price,4)} | RSI: {round(rsi,1)} | MA10: ${round(ma,4)}\n"

        if rsi < 30 and price < ma:
            msg += "🤖 AI: Сильная точка входа (перепродан)"
            return msg, True
        elif rsi > 70 and price > ma:
            msg += "🤖 AI: Время фиксировать прибыль"
            return msg, False
        else:
            msg += "🤖 AI: Нейтральная зона"
            return msg, False
    except Exception as e:
        return f"{symbol}: ❌ Ошибка AI-прогноза ({str(e)})", False

def auto_signal():
    full_msg = "🤖 [AI Автосигнал — 15 мин]:\n\n"
    for token in TOKENS:
        msg, do_trade = ai_signal(token)
        full_msg += msg + "\n\n"
        if do_trade:
            price = get_token_price(token)
            trade = {
                "token": token,
                "price": price,
                "amount": TRADE_AMOUNT,
                "timestamp": time.strftime("%Y-%m-%d %H:%M")
            }
            trades.append(trade)
            save_trades()
            bot.send_message(USER_ID, f"✅ Автосделка: Куплено {token} на ${TRADE_AMOUNT} по ${price}")
    bot.send_message(USER_ID, full_msg)

def schedule_loop():
    schedule.every(15).minutes.do(auto_signal)
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start', 'menu'])
def send_menu(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📈 AI сигналы", callback_data="all_signals"),
        InlineKeyboardButton("📉 График SOL", callback_data="chart_SOL"),
        InlineKeyboardButton("🧾 История сделок", callback_data="history")
    )
    for token in TOKENS:
        markup.add(InlineKeyboardButton(f"💰 Цена {token}", callback_data=token))
    bot.send_message(message.chat.id, "👋 Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "all_signals":
        full_msg = ""
        for token in TOKENS:
            msg, _ = ai_signal(token)
            full_msg += msg + "\n\n"
        bot.send_message(call.message.chat.id, full_msg)
    elif call.data == "history":
        if not trades:
            bot.send_message(call.message.chat.id, "📉 Сделок пока нет.")
        else:
            text = "🧾 История сделок:\n\n"
            for t in trades[-10:]:
                text += f"{t['timestamp']} — {t['token']} — ${t['amount']} по ${t['price']}\n"
            bot.send_message(call.message.chat.id, text)
    elif call.data.startswith("chart_"):
        symbol = call.data.split("_")[1]
        chart = build_chart(symbol)
        if chart:
            bot.send_photo(call.message.chat.id, chart, caption=f"📉 График {symbol}")
        else:
            bot.send_message(call.message.chat.id, "❌ Не удалось построить график.")
    elif call.data in TOKENS:
        price = get_token_price(call.data)
        bot.send_message(call.message.chat.id, f"💰 Текущая цена {call.data}: ${price}")

# 🔁 Запуск в фоне
threading.Thread(target=schedule_loop, daemon=True).start()
bot.polling()
