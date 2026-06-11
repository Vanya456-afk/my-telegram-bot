import telebot
import os
import random
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- РАСШИРЕННАЯ БАЗА ДАННЫХ ИГРОКОВ ---
players = {}

def get_player(user_id, username="Игрок"):
    if user_id not in players:
        players[user_id] = {
            'name': username,
            'coins': 1500,        # Стартовые монеты
            'gems': 100,          # Стартовые гемы для скинов/ящиков
            'cups': 0, 
            'wins': 0,
            'bg': "Classic Blue", # Дефолтная тема профиля (Идея 9)
            'brawlers': {         # Структура: "Имя": уровень_силы (Идея 8)
                "Шелли": 1
            },
            'skins': [],          # Коллекция unlocked скинов (Идея 4, 5, 10)
            'used_promos': []     # Использованные промокоды (Идея 5)
        }
    return players[user_id]

# Темы профиля (Идея 9)
THEMES = {
    "Classic Blue": "🟦 СТАНДАРТНЫЙ СИНИЙ ПРОФИЛЬ 🟦",
    "Brawl Ball Stadium": "⚽ СТАДИОН БРОУЛБОЛА ⚽",
    "Wild West": "🌵 ДИКИЙ ЗАПАД 🌵",
    "Golden Arena": "✨ ЗОЛОТАЯ АРЕНА ✨"
}

# --- КЛАВИАТУРЫ ---
def get_main_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("👤 Профиль", "⚔️ В бой!", "🎨 Кастомизация", "🛍 Магазин", "🏆 Топ", "🎟️ Ввести Промокод")
    return markup

# --- КОМАНДА /START ---
@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name or "Игрок"
    get_player(message.from_user.id, name)
    
    welcome_text = (
        f"Добро пожаловать в Vasanin Brawl, {name}!\n\n"
        f"У нас появились банды, прокачка, кастомизация профилей и секретные промокоды!\n"
        f"Жми кнопки меню, чтобы начать свой путь к мастерству."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_markup())

# --- ОБРАБОТКА ИГРОВОЙ ЛОГИКИ ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    user = get_player(user_id, name)
    user['name'] = name 

    # 1. 👤 РАЗДЕЛ: ПРОФИЛЬ + ТЕМЫ (Идея 9)
    if message.text == "👤 Профиль":
        brawlers_list = [f"{b} ({lvl} ур.)" for b, lvl in user['brawlers'].items()]
        brawlers_str = ", ".join(brawlers_list)
        skins_str = ", ".join(user['skins']) if user['skins'] else "Нет кастомных скинов"
        
        # Рендерим красивый заголовок в зависимости от выбранной темы
        theme_header = THEMES.get(user['bg'], THEMES["Classic Blue"])
        
        info = (
            f"{theme_header}\n"
            f"👤 Игрок: {user['name']}\n"
            f"🏆 Кубки: {user['cups']}\n"
            f"💰 Монеты: {user['coins']} | 💎 Гемы: {user['gems']}\n"
            f"📈 Побед в боях: {user['wins']}\n\n"
            f"🦸‍♂️ Твоя команда: {brawlers_str}\n"
            f"👕 Твои скины: {skins_str}\n"
            f"━━━━━━━━━━━━━━"
        )
        bot.send_message(message.chat.id, info, reply_markup=get_main_markup())

    # 2. ⚔️ РАЗДЕЛ: РЕЖИМЫ БОЯ (Идея 3)
    elif message.text == "⚔️ В бой!":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🌵 Столкновение", "⚽ Броулбол", "💎 Захват Кристаллов", "💰 Ограбление", "Назад")
        bot.send_message(message.chat.id, "🕹️ Выбери активный игровой режим:", reply_markup=markup)

    elif message.text in ["🌵 Столкновение", "⚽ Броулбол", "💎 Захват Кристаллов", "💰 Ограбление"]:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("Обычный бой", "Назад") # Сюда следующим шагом прикрутим Множитель (Идея 2)
        bot.send_message(message.chat.id, f"Выбран режим: {message.text}\n\nВыбери тип боя:", reply_markup=markup)

    elif message.text == "Обычный бой":
        is_win = random.choice([True, False])
        current_brawler = random.choice(list(user['brawlers'].keys()))
        
        if is_win:
            user['cups'] += 10
            user['coins'] += 30
            user['wins'] += 1
            result = f"✅ {current_brawler} тащит катку! Победа!\n🏆 +10 кубков, 💰 +30 монет."
        else:
            user['cups'] = max(0, user['cups'] - 7)
            result = f"❌ Твою команду зажали на респе... Поражение.\n📉 -7 кубков."
            
        bot.send_message(message.chat.id, f"⚔️ Результат симуляции:\n\n{result}", reply_markup=get_main_markup())

    # 3. 🎨 РАЗДЕЛ: КАСТОМИЗАЦИЯ ТЕМЫ (Идея 9)
    elif message.text == "🎨 Кастомизация":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add("Купить Стадион ⚽ (50 💎)", "Купить Дикий Запад 🌵 (50 💎)", "Купить Золотую Арену ✨ (50 💎)", "Назад")
        bot.send_message(message.chat.id, "🎨 Измени фон своей карточки профиля!\nКаждая тема стоит 50 💎. Выбери стиль:", reply_markup=markup)

    elif "Купить" in message.text:
        target_bg = ""
        if "Стадион" in message.text: target_bg = "Brawl Ball Stadium"
        elif "Дикий Запад" in message.text: target_bg = "Wild West"
        elif "Золотую Арену" in message.text: target_bg = "Golden Arena"
        
        if user['bg'] == target_bg:
            bot.send_message(message.chat.id, "❌ У тебя уже установлена эта тема!", reply_markup=get_main_markup())
        elif user['gems'] < 50:
            bot.send_message(message.chat.id, "❌ Недостаточно гемов! Зарабатывай их или жди ивентов.", reply_markup=get_main_markup())
        else:
            user['gems'] -= 50
            user['bg'] = target_bg
            bot.send_message(message.chat.id, f"🎉 Тема успешно куплена и применена! Проверь свой 👤 Профиль.", reply_markup=get_main_markup())

    # 4. 🎟️ РАЗДЕЛ: ПРОМОКОД НА ЛУМИ (Идея 4 и 5)
    elif message.text == "🎟️ Ввести Промокод":
        bot.send_message(message.chat.id, "Отправь секретный промокод в ответном сообщении:")

    elif message.text == "АняСамаяЛучшая":
        if "АняСамаяЛучшая" in user['used_promos']:
            bot.send_message(message.chat.id, "❌ Ты уже активировал этот промокод!", reply_markup=get_main_markup())
        else:
            user['used_promos'].append("АняСамаяЛучшая")
            # Разблокируем Хроматического бойца Луми (Идея 4)
            user['brawlers']["❄️ Луми"] = 1
            # Добавляем все 3 эксклюзивных скина (Идея 5)
            user['skins'].extend(["«Новогодняя Луми»", "«Кибер-Луми»", "«Королева Луми»"])
            
            reward_text = (
                "🎉 ПРОМОКОД УСПЕШНО АКТИВИРОВАН! 🎉\n\n"
                "❄️ Хроматический боец Луми добавлен в твою команду (1 уровень силы)!\n"
                "👕 Разблокировано 3 премиум скина:\n"
                "• Новогодняя Луми\n"
                "• Кибер-Луми\n"
                "• Королева Луми"
            )
            bot.send_message(message.chat.id, reward_text, reply_markup=get_main_markup())

    # 5. СТАНДАРТНЫЕ РАЗДЕЛЫ
    elif message.text == "🛍 Магазин":
        bot.send_message(message.chat.id, "🛍 Магазин готовится к закупке Мегаящиков! Скоро здесь можно будет закупаться оптом.", reply_markup=get_main_markup())

    elif message.text == "🏆 Топ":
        # Сортировка LIVE топа по кубкам
        sorted_players = sorted(players.values(), key=lambda x: x['cups'], reverse=True)
        top_msg = "🏆 Топ 10 Игроков\n━━━━━━━━━━━━━━\n"
        for i in range(10):
            top_msg += "Боец\n"
            if i < len(sorted_players):
                p = sorted_players[i]
                top_msg += f"#{i+1} {p['name']}\n   {p['cups']} кубков  {p['coins']} монет  {p['wins']} побед\n"
            else:
                top_msg += f"#{i+1} Новичок\n   0 кубков  1500 монет  0 побед\n"
        bot.send_message(message.chat.id, top_msg, reply_markup=get_main_markup())

    elif message.text == "Назад":
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_markup())
    else:
        bot.send_message(message.chat.id, "Используй кнопки меню!", reply_markup=get_main_markup())

@app.route('/')
def home():
    return "Bot is running"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
