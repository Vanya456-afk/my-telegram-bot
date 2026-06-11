import telebot
import os
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Наше меню
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Создаем кнопки
    btn1 = telebot.types.KeyboardButton("🏆 Топ")
    btn2 = telebot.types.KeyboardButton("🛍 Магазин")
    btn3 = telebot.types.KeyboardButton("📦 Ящики")
    btn4 = telebot.types.KeyboardButton("⚔️ В бой")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)

# Обработка нажатий
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "🏆 Топ":
        bot.send_message(message.chat.id, "📊 Вот список лучших игроков:\n1. Игрок1 - 1000 очков\n2. Игрок2 - 950 очков")
    elif message.text == "🛍 Магазин":
        bot.send_message(message.chat.id, "🛒 Добро пожаловать в магазин! Что купим?")
    elif message.text == "📦 Ящики":
        bot.send_message(message.chat.id, "🎁 Ты открыл ящик и получил 50 монет!")
    elif message.text == "⚔️ В бой":
        bot.send_message(message.chat.id, "⚡️ Поиск противника... Начинаем битву!")
    else:
        bot.send_message(message.chat.id, "Не понимаю. Нажми /start, чтобы открыть меню.")

@app.route('/')
def home():
    return "Bot is active"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
