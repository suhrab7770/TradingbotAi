import requests
import pandas as pd
import time
from datetime import datetime

CMC_API_KEY = "bd5f81f5-9e2c-4483-8060-ff7eb41b3a54"
HEADERS = {
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

def get_top_100_cmc():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        "start": "1",
        "limit": "100",
        "convert": "USD"
    }
    res = requests.get(url, headers=HEADERS, params=params).json()
    return res.get("data", [])

def get_historical_cmc(symbol):
    url = f"https://api.coincap.io/v2/assets/{symbol}/history"
    params = {
        "interval": "h1",  # 1 час
        "start": int((time.time() - 2*24*60*60) * 1000),  # последние 2 дня
        "end": int(time.time() * 1000)
    }
    try:
        res = requests.get(url, params=params).json()
        data = res.get("data", [])
        if not data:
            return None
        df = pd.DataFrame(data)
        df["priceUsd"] = df["priceUsd"].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.rename(columns={"priceUsd": "price"}, inplace=True)
        return df
    except:
        return None

def calculate_rsi(df, period=14):
    delta = df["price"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_top_100():
    results = []
    coins = get_top_100_cmc()
    for coin in coins[:25]:  # ограничим первыми 25 монетами для скорости
        try:
            name = coin["name"]
            symbol = coin["symbol"].lower()
            price = float(coin["quote"]["USD"]["price"])

            df = get_historical_cmc(symbol)
            if df is None or len(df) < 20:
                continue

            df["MA10"] = df["price"].rolling(10).mean()
            df["RSI"] = calculate_rsi(df)
            rsi = df["RSI"].iloc[-1]
            ma10 = df["MA10"].iloc[-1]

            if rsi < 30 and price > ma10:
                signal = "✅ BUY"
                sl = round(price * 0.95, 6)
                tp = round(price * 1.1, 6)
                lev = "x3"
            elif rsi > 70 and price < ma10:
                signal = "❌ SELL"
                sl = round(price * 1.05, 6)
                tp = round(price * 0.9, 6)
                lev = "x5"
            else:
                continue  # только BUY и SELL

            result = f"{signal}: {symbol.upper()} | Цена: ${round(price, 6)}\nSL: ${sl} | TP: ${tp} | Плечо: {lev}"
            results.append(result)
            time.sleep(1)
        except Exception as e:
            continue
    return results
