# bot.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os

# Твои ключи от MEXC (вставь сам!)
MEXC_API_KEY = os.getenv("MEXC_API_KEY")
MEXC_API_SECRET = os.getenv("MEXC_API_SECRET")

# Главная команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Баланс", callback_data='balance')],
        [InlineKeyboardButton("💰 Купить", callback_data='buy'),
         InlineKeyboardButton("🔻 Продать", callback_data='sell')],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
        [InlineKeyboardButton("🤖 AI-помощник", callback_data='ai')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Я твой трейдинг-бот на MEXC 💹", reply_markup=reply_markup)

# Обработка нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'balance':
        # Тут будет функция получения баланса
        await query.edit_message_text("💼 Твой баланс: ...")
    elif query.data == 'buy':
        await query.edit_message_text("Введите команду /buy <пара> <кол-во>")
    elif query.data == 'sell':
        await query.edit_message_text("Введите команду /sell <пара> <кол-во>")
    elif query.data == 'settings':
        await query.edit_message_text("⚙️ Настройки: Пока пусто...")
    elif query.data == 'ai':
        await query.edit_message_text("🤖 AI поможет тебе в трейдинге! (в разработке)")

# Запуск бота
def main():
    app = ApplicationBuilder().token("ТОКЕН_ТВОЕГО_ТЕЛЕГРАМ_БОТА").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == '__main__':
    main()

