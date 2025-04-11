import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import threading
import schedule
import time
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

TOKEN = '7580720199:AAE1mgv_7D2j7SFnEug57Ja5Xit7YN861BE'
USER_ID = 2036758982
bot = telebot.TeleBot(TOKEN)
TOKENS = ["SOL", "JUP", "BONK", "PYTH"]

# CoinGecko ID-словарь
COINGECKO_IDS = {
    "SOL": "solana",
    "JUP": "jupiter-exchange",
    "BONK": "bonk",
    "PYTH": "pyth-network"
}

def get_token_price(symbol):
    try:
        url = f"https://price.jup.ag/v4/price?ids={symbol}"
        res = requests.get(url).json()
        return round(res['data'][symbol]['price'], 6)
    except Exception as e:
        print(f"Price fetch error for {symbol}: {e}")
        return "н/д"

def get_historical_prices(symbol="SOL"):
    try:
        cg_id = COINGECKO_IDS.get(symbol, symbol.lower())
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart?vs_currency=usd&days=2"
        res = requests.get(url).json()
        if "prices" not in res:
            raise ValueError(f"No 'prices' found in response for {symbol} (ID: {cg_id})")
        prices = res["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["price"] = df["price"].astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        print(f"Chart error for {symbol}: {e}")
        raise

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
        print("Chart error:", e)
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
        elif rsi > 70 and price > ma:
            msg += "🤖 AI: Время фиксировать прибыль"
        else:
            msg += "🤖 AI: Нейтральная зона"
        return msg
    except Exception as e:
        return f"{symbol}: ❌ Ошибка AI-прогноза ({str(e)})"

def auto_signal():
    signals = [ai_signal(token) for token in TOKENS]
    message = "🤖 [AI Автосигнал — 15 мин]:\n\n" + "\n\n".join(signals)
    bot.send_message(USER_ID, message)


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
        InlineKeyboardButton("💰 Цена SOL", callback_data="SOL"),
        InlineKeyboardButton("💰 Цена JUP", callback_data="JUP"),
        InlineKeyboardButton("💰 Цена BONK", callback_data="BONK"),
        InlineKeyboardButton("💰 Цена PYTH", callback_data="PYTH")
    )
    bot.send_message(message.chat.id, "👋 Меню трейдера:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "all_signals":
        signals = [ai_signal(token) for token in TOKENS]
        message = "📊 AI-сигналы на сейчас:\n\n" + "\n\n".join(signals)
        bot.send_message(call.message.chat.id, message)
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


# Запуск планировщика в фоне
threading.Thread(target=schedule_loop, daemon=True).start()
bot.polling()
