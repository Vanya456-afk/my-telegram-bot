import telebot
import os
from flask import Flask

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Простая обработка старта
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Кнопка 1", "Кнопка 2")
    bot.send_message(message.chat.id, "Бот работает! Нажми кнопку:", reply_markup=markup)

# Обработка нажатий
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    bot.send_message(message.chat.id, f"Бот получил: {message.text}")

# Веб-сервер для Render (чтобы он не спал)
@app.route('/')
def home():
    return "Bot is running"

if __name__ == "__main__":
    # Запускаем бота в обычном режиме
    # Примечание: на Render лучше использовать один поток
    import threading
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
