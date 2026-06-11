import telebot
import os
from flask import Flask
import threading

# Токен берется из настроек Render (Environment Variables)
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Главное меню
@bot.message_handler(commands=['start'])
def start(message):
    # Получаем имя пользователя
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"Добро пожаловать в Vasanin Brawl, {user_name}!\n\n"
        "💰 Стартовый капитал: 1000 монет\n"
        "Побеждай в боях, открывай ящики, собирай бойцов и кубки!\n\n"
        "Используй промокод START для бонуса!"
    )
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Кнопка 1", "Кнопка 2", "Магазин", "Топ", "Ящики", "В бой")
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# Логика ответов
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "Топ":
        top_list = """
🏆 Топ 10 Игроков
━━━━━━━━━━━━━━
Боец
#1 Легенда Бравла
   0 кубков  0 монет  0 побед
Боец
#2 Легенда Бравла
   0 кубков  0 монет  0 побед
Боец
#3 Легенда Бравла
   0 кубков  0 монет  0 побед
Боец
#4 Мастер
   0 кубков  0 монет  0 побед
Боец
#5 Боец
   0 кубков  0 монет  0 побед
Боец
#6 Новичок
   0 кубков  0 монет  0 побед
Боец
#7 Новичок
   0 кубков  0 монет  0 побед
Боец
#8 Новичок
   0 кубков  0 монет  0 побед
Боец
#9 Новичок
   0 кубков  0 монет  0 побед
Боец
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

# Веб-сервер для Render
@app.route('/')
def home():
    return "Bot is running"

if __name__ == "__main__":
    # Запуск бота
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    # Запуск Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
