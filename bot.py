import telebot
import os
from flask import Flask
import threading

# Токен берется из настроек Render (Environment Variables)
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Главное меню со всеми кнопками
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Кнопка 1", "Кнопка 2", "Магазин", "Топ", "Ящики", "В бой")
    bot.send_message(message.chat.id, "Привет! Выбирай, что делать:", reply_markup=markup)

# Логика ответов
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "Топ":
        top_list = """
🏆 Топ 10 Игроков
━━━━━━━━━━━━━━
#1 Легенда Бравла
   0 кубков  0 монет  0 побед
#2 Легенда Бравла
   0 кубков  0 монет  0 побед
#3 Легенда Бравла
   0 кубков  0 монет  0 побед
#4 Мастер
   0 кубков  0 монет  0 побед
#5 Боец
   0 кубков  0 монет  0 побед
#6 Новичок
   0 кубков  0 монет  0 побед
#7 Новичок
   0 кубков  0 монет  0 побед
#8 Новичок
   0 кубков  0 монет  0 побед
#9 Новичок
   0 кубков  0 монет  0 побед
#10 Новичок
   0 кубков  0 монет  0 побед
"""
        bot.send_message(message.chat.id, top_list)
        
    elif message.text == "Магазин":
        bot.send_message(message.chat.id, "🛒 Добро пожаловать в магазин!")
    elif message.text == "Ящики":
        bot.send_message(message.chat.id, "📦 Ты открыл ящик!")
    elif message.text == "В бой":
        bot.send_message(message.chat.id, "⚔️ Поиск противника...")
    else:
        bot.send_message(message.chat.id, f"Ты нажал: {message.text}")

# Веб-сервер, чтобы Render не выключал бота
@app.route('/')
def home():
    return "Bot is running"

if __name__ == "__main__":
    # Запуск бота в отдельном потоке
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    # Запуск Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
