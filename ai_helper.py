# ai_helper.py
def analyze_message(msg, indicators):
    msg = msg.lower()
    rsi = indicators["rsi"]
    ma = indicators["ma"]
    price = indicators["price"]

    if "купить" in msg or "вход" in msg:
        if rsi < 30 and price < ma:
            return "🧠 Это выглядит как хорошая точка входа (перепродан, цена ниже MA10)."
        elif 30 <= rsi <= 50:
            return "🤖 Может быть, но сигнал не самый сильный. RSI в нейтральной зоне."
        else:
            return "⚠️ Сейчас лучше подождать. RSI слишком высок."

    elif "продать" in msg or "выход" in msg:
        if rsi > 70 and price > ma:
            return "💡 Сейчас похоже на хороший момент для фиксации прибыли!"
        else:
            return "🔄 Не спеши продавать. Сигналов к выходу нет."

    elif "что думаешь" in msg or "анализ" in msg:
        return f"📊 RSI: {round(rsi,1)}, MA10: {round(ma,2)}, Цена: {round(price,2)} — Всё стабильно, наблюдаем."

    else:
        return "🤖 Я могу помочь с анализом! Напиши: 'Купить SOL?', 'Продать BONK?' или 'Что думаешь про PYTH?'"
