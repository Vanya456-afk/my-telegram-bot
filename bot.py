import telebot
import os
import random
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Функция главного меню (вынесена отдельно для удобства)
def main_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Кнопка 1", "Кнопка 2", "Магазин", "Топ", "Ящики", "В бой")
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"Добро пожаловать в Vasanin Brawl, {user_name}!\n\n"
        "💰 Стартовый капитал: 1000 монет\n"
        "Используй промокод START для бонуса!"
    )
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Кнопка 1", "Кнопка 2", "Магазин", "Топ", "Ящики", "В бой")
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "Топ":
        bot.send_message(message.chat.id, "🏆 Топ 10 Игроков... (список)")
        
    elif message.text == "В бой":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add("Столкновение", "Захват кристаллов", "Назад")
        bot.send_message(message.chat.id, "Выбери режим:", reply_markup=markup)

    elif message.text in ["Столкновение", "Захват кристаллов"]:
        info_text = (
            f"🎮 {message.text}\n\n"
            "🎟 Билеты: 0\n"
            "⚡️ Множитель: победа даёт ×1 кубков и монет, поражение — ×1 штраф.\n\n"
            "Выбери тип боя:"
        )
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("Обычный", "Ранговый", "Назад")
        bot.send_message(message.chat.id, info_text, reply_markup=markup)

    elif message.text in ["Обычный", "Ранговый"]:
        bot.send_message(message.chat.id, f"⚔️ Начало боя в режиме {message.text}...")
        
    elif message.text == "Назад":
        main_menu(message)
    else:
        bot.send_message(message.chat.id, f"Ты нажал: {message.text}")

@app.route('/')
def home():
    return "Bot is running"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
