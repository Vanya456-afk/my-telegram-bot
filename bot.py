import telebot
import os
from flask import Flask

TOKEN = '8351938763:AAEQSmDbJaoPxhcOJeOen6TtyRq0SHBafoA'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Основной код бота
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот работает на Render!")

# Это нужно для Render, чтобы он видел, что бот «жив»
@app.route('/')
def home():
    return "Бот работает!"

if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    import threading
    threading.Thread(target=bot.infinity_polling).start()
    # Запускаем Flask на порту, который требует Render
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
