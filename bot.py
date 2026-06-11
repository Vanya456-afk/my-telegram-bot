import telebot
import os
import random
from flask import Flask
import threading
import datetime

# Инициализация бота и веб-сервера
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- ГЛОБАЛЬНАЯ БАЗА ДАННЫХ В ПАМЯТИ ---
players = {}
clans = {}

# --- ЕЩЕ БОЛЬШЕ КУЛЬТОВЫХ БОЙЦОВ (30+ ПЕРСОНАЖЕЙ) ---
ALL_BRAWLERS = {
    # Редкие
    "Шелли": {"rarity": "🟢 Редкий", "bonus": "Стабильность (+5% к шансу победы в боях)"},
    "Кольт": {"rarity": "🟢 Редкий", "bonus": "Шоумен (+20% к золоту за любые победы)"},
    "Булл": {"rarity": "🟢 Редкий", "bonus": "Танк (В рейдах на Робо-Босса наносит на 35% больше урона)"},
    "Эль Примо": {"rarity": "🟢 Редкий", "bonus": "Гроза кубиков (+20% к выигрышу в Казино Старр)"},
    "Поко": {"rarity": "🟢 Редкий", "bonus": "Целитель (Уменьшает время перезарядки рейдов до 45 минут)"},
    "Роза": {"rarity": "🟢 Редкий", "bonus": "Флора (+10% к золоту из ежедневных наград)"},
    "Барли": {"rarity": "🟢 Редкий", "bonus": "Сироп (35% шанс удвоить монеты при проигрыше в Столкновении)"},

    # Сверхредкие
    "Брок": {"rarity": "🔵 Сверхредкий", "bonus": "Ракетчик (+25% к опыту (XP) в Vasanin Pass)"},
    "Рико": {"rarity": "🔵 Сверхредкий", "bonus": "Рикошет (30% шанс вернуть ставку в Brawl TV при проигрыше)"},
    "Джесси": {"rarity": "🔵 Сверхредкий", "bonus": "Инженер (Приносит +5 кубков при победе в Броулболе)"},
    "Динамайк": {"rarity": "🔵 Сверхредкий", "bonus": "Подрывник (Приносит +50 монет при победе в Столкновении)"},
    "Пенни": {"rarity": "🔵 Сверхредкий", "bonus": "Пират (Шанс получить х2 золото при открытии Starr Drops)"},
    "Карл": {"rarity": "🔵 Сверхредкий", "bonus": "Геолог (+10% шанс выбить Гемы вместо золота из Starr Drops)"},
    "Гас": {"rarity": "🔵 Сверхредкий", "bonus": "Дух (Защищает от падения кубков, если их меньше 150)"},

    # Эпические
    "Эдгар": {"rarity": "💜 Эпический", "bonus": "Агро-хил (Высокий шанс победы, но приносит на 3 кубка меньше)"},
    "Пайпер": {"rarity": "💜 Эпический", "bonus": "Снайпер (Каждый уровень силы дает +2% к шансу победы)"},
    "Биби": {"rarity": "💜 Эпический", "bonus": "Хоум-ран (+10% к базовой скорости прокачки кубков)"},
    "Фрэнк": {"rarity": "💜 Эпический", "bonus": "Тяжеловес (+500 урона по Робо-Боссу)"},
    "Бо": {"rarity": "💜 Эпический", "bonus": "Парение (Приносит +5 XP Пасса даже при жестком поражении)"},
    "Гром": {"rarity": "💜 Эпический", "bonus": "Радиус (Увеличивает награду в Броулболе на +30 монет)"},

    # Мифические
    "Мортис": {"rarity": "🟥 Мифический", "bonus": "Хардкор (+15 кубков за победу, но шанс выигрыша снижен)"},
    "Тара": {"rarity": "🟥 Мифический", "bonus": "Предсказание (Показывает скрытый бонус в Starr Drops)"},
    "Мелоди": {"rarity": "🟥 Мифический", "bonus": "Ноты вдохновения (+30% к опыту пасса за победу в Броулболе)"},
    "Мико": {"rarity": "🟥 Мифический", "bonus": "Прыгун (Полный иммунитет к потере кубков, если кубков меньше 300)"},
    "Лили": {"rarity": "🟥 Мифический", "bonus": "Вспышка (Увеличивает шанс критического Starr Drop на 15%)"},
    "Мо": {"rarity": "🟥 Мифический", "bonus": "Бурение (+100 монет за каждую клановую активность)"},

    # Легендарные
    "Леон": {"rarity": "🟨 Легендарный", "bonus": "Инвиз (Снижает потерю кубков при поражениях до -2 🏆)"},
    "Спайк": {"rarity": "🟨 Легендарный", "bonus": "Кактус (+50% к золоту из любых Starr Drops)"},
    "Кит": {"rarity": "🟨 Легендарный", "bonus": "Помощник (Удваивает кубки, если играешь в команде/есть друзья)"},
    "Корделиус": {"rarity": "🟨 Легендарный", "bonus": "Царство грибов (Каждый Starr Drop гарантированно дает +5 гемов)"},
    "Драко": {"rarity": "🟨 Легендарный", "bonus": "Драконий триумф (+25 кубков за победу в Столкновении)"},
    "Кенджи": {"rarity": "🟨 Легендарный", "bonus": "Путь самурая (+40% к шансу выбить нового бойца из ящиков)"},

    # Хроматические / Особые
    "Вольт": {"rarity": "🌟 Хроматический", "bonus": "Максимум силы (С каждым уровнем силы дает +5% к золоту)"},
    "Гавс": {"rarity": "🌟 Хроматический", "bonus": "Провизия (Раз в день дает бесплатный билет на рейд)"}
}

def get_player(user_id, username="Игрок"):
    if user_id not in players:
        players[user_id] = {
            'name': username,
            'coins': 2000,
            'gems': 200,
            'cups': 0,
            'pass_xp': 0,
            'pass_lvl': 1,
            'clan': None,
            'wins': 0,
            'claimed_pass_rewards': [],
            'claimed_trophies': [],
            'last_daily': None,
            'last_boss_attack': None,
            'quests': [
                {"id": 1, "desc": "Сыграть бой в Столкновении", "done": False, "reward": 100},
                {"id": 2, "desc": "Открыть Starr Drop", "done": False, "reward": 150}
            ],
            'bg': "Classic Blue",
            'brawlers': {"Шелли": 1}, 
            'skins': [],
            'used_promos': [],
            'friends': [],
            'selected_brawler': "Шелли"
        }
    return players[user_id]

user_states = {}

THEMES = {
    "Classic Blue": "🟦 КЛАССИЧЕСКИЙ СИНИЙ ПРОФИЛЬ 🟦",
    "Brawl Ball Stadium": "⚽ СТАДИОН БРОУЛБОЛА ⚽",
    "Wild West": "🌵 ДИКИЙ ЗАПАД 🌵",
    "Golden Arena": "✨ ЗОЛОТАЯ АРЕНА ✨"
}

def get_main_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⚔️ В бой!", "👤 Профиль")
    markup.add("🛍 Магазин", "✨ Starr Drops")
    markup.add("🎫 Промокоды", "🏆 Топ Игроков")
    markup.add("🌟 Vasanin Pass", "🏆 Путь к Славе")
    markup.add("🎨 Кастомизация", "👥 Сообщество")
    markup.add("🛡️ Кланы", "🎁 Награда")
    markup.add("📺 Brawl TV", "📜 Квесты")
    return markup

# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or f"User_{user_id}"
    get_player(user_id, name)
    bot.send_message(message.chat.id, f"🔥 Добро пожаловать! Огромный ростер персонажей готов к битвам. Жми '⚔️ В бой!', чтобы выбрать бойца!", reply_markup=get_main_markup())

# --- ОБРАБОТКА CALLBACK ИНЛАЙН КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_player(user_id)
    
    # Клик по бойцу в меню выбора: показывает характеристики
    if call.data.startswith("view_brawler_"):
        brawler = call.data.replace("view_brawler_", "")
        lvl = user['brawlers'].get(brawler, 1)
        b_info = ALL_BRAWLERS.get(brawler, {"rarity": "🟢 Неизвестно", "bonus": "Нет"})
        
        text = (
            f"ℹ️ **КАРТОЧКА ПЕРСОНАЖА: {brawler}**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⭐ Редкость: {b_info['rarity']}\n"
            f"🧪 Текущий Уровень Силы: **{lvl}/11**\n"
            f"⚡ Пассивная способность:\n*{b_info['bonus']}*\n"
        )
        
        inline_confirm = telebot.types.InlineKeyboardMarkup()
        inline_confirm.add(telebot.types.InlineKeyboardButton(text=f"🎯 Взять {brawler} в бой", callback_data=f"equip_brawler_{brawler}"))
        inline_confirm.add(telebot.types.InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_selection"))
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=inline_confirm, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    # Окончательное снаряжение бойца
    elif call.data.startswith("equip_brawler_"):
        brawler = call.data.replace("equip_brawler_", "")
        user['selected_brawler'] = brawler
        
        markup_battle = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup_battle.add("🌵 Одиночное Столкновение", "⚽ Броулбол", "Назад")
        
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, f"✅ **{brawler} успешно экипирован!**\nВыбирай игровой режим на клавиатуре ниже 👇", reply_markup=markup_battle)
        bot.answer_callback_query(call.id)

    # Кнопка возврата к списку
    elif call.data == "back_to_selection":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        inline_choose = telebot.types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for b in user['brawlers'].keys():
            status = "🎯 " if user['selected_brawler'] == b else ""
            rarity_ico = ALL_BRAWLERS.get(b, {"rarity": "🟢"})["rarity"].split()[0]
            buttons.append(telebot.types.InlineKeyboardButton(text=f"{status}{rarity_ico} {b}", callback_data=f"view_brawler_{b}"))
        inline_choose.add(*buttons)
        
        bot.send_message(call.message.chat.id, "🦸‍♂️ **ВЫБОР БОЙЦА**\nКликни на персонажа из своей коллекции, чтобы посмотреть его бонусы и взять в бой:", reply_markup=inline_choose)
        bot.answer_callback_query(call.id)

    # Прокачка силы из профиля
    elif call.data.startswith("up_"):
        brawler = call.data.replace("up_", "")
        curr_lvl = user['brawlers'][brawler]
        if curr_lvl >= 11:
            bot.answer_callback_query(call.id, "❌ Максимальная сила (11 уровень)!", show_alert=True)
            return
        cost = curr_lvl * 400
        if user['coins'] < cost:
            bot.answer_callback_query(call.id, f"❌ Нужно монет: {cost} 💰", show_alert=True)
        else:
            user['coins'] -= cost
            user['brawlers'][brawler] += 1
            bot.answer_callback_query(call.id, "🎉 Сила повышена!")
            bot.send_message(call.message.chat.id, f"🧪 **{brawler}** успешно апнут до **{user['brawlers'][brawler]} уровня силы**!")

    # Система Starr Drops
    elif call.data == "roll_starr_drop":
        rarities = ["⚡ РЕДКИЙ", "🔷 СВЕРХРЕДКИЙ", "💜 ЭПИЧЕСКИЙ", "🟥 МИФИЧЕСКИЙ", "🟨 ЛЕГЕНДАРНЫЙ"]
        roll = random.random()
        
        if roll < 0.45: final_rarity = rarities[0]
        elif roll < 0.75: final_rarity = rarities[1]
        elif roll < 0.90: final_rarity = rarities[2]
        elif roll < 0.97: final_rarity = rarities[3]
        else: final_rarity = rarities[4]

        coins_add = random.randint(100, 250)
        gems_add = 0
        brawler_drop = None

        if final_rarity == "🔷 СВЕРХРЕДКИЙ": coins_add = random.randint(250, 500)
        elif final_rarity == "💜 ЭПИЧЕСКИЙ": coins_add = random.randint(500, 800); gems_add = random.randint(5, 10)
        elif final_rarity == "🟥 МИФИЧЕСКИЙ": coins_add = random.randint(800, 1500); gems_add = random.randint(10, 30)
        elif final_rarity == "🟨 ЛЕГЕНДАРНЫЙ":
            gems_add = random.randint(30, 80)
            locked = [b for b in ALL_BRAWLERS.keys() if b not in user['brawlers']]
            if locked: brawler_drop = random.choice(locked)

        if user['selected_brawler'] == "Спайк": coins_add = int(coins_add * 1.5)
        if user['selected_brawler'] == "Корделиус": gems_add += 5
        if user['selected_brawler'] == "Лили":
            if random.random() < 0.15: coins_add *= 2

        user['coins'] += coins_add
        user['gems'] += gems_add
        if brawler_drop: user['brawlers'][brawler_drop] = 1

        for q in user['quests']:
            if "Starr Drop" in q['desc']: q['done'] = True

        res_drop = f"✨ **СТАРР ДРОП ОТКРЫТ!** ✨\n\nРедкость: **{final_rarity}**\n━━━━━━━━━━━━━━━\n💰 Монеты: +{coins_add}\n💎 Гемы: +{gems_add}"
        if brawler_drop:
            res_drop += f"\n\n🔥 🌟 **ЛЕГЕНДАРНЫЙ ДРОП:** Разблокирован новый боец: **{brawler_drop}** ({ALL_BRAWLERS[brawler_drop]['rarity']})!"
        
        bot.send_message(call.message.chat.id, res_drop)
        bot.answer_callback_query(call.id)

# --- ОБРАБОТКА ТЕКСТА ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    user = get_player(user_id, name)

    # Главное меню выбора бойца перед каткой
    if message.text == "⚔️ В бой!":
        inline_choose = telebot.types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for b in user['brawlers'].keys():
            status = "🎯 " if user['selected_brawler'] == b else ""
            rarity_ico = ALL_BRAWLERS.get(b, {"rarity": "🟢"})["rarity"].split()[0]
            buttons.append(telebot.types.InlineKeyboardButton(text=f"{status}{rarity_ico} {b}", callback_data=f"view_brawler_{b}"))
        inline_choose.add(*buttons)
        
        bot.send_message(message.chat.id, "🦸‍♂️ **ВЫБОР БОЙЦА**\nКликни на персонажа из своей коллекции, чтобы посмотреть его бонусы и взять в бой:", reply_markup=inline_choose)

    elif message.text in ["🌵 Одиночное Столкновение", "⚽ Броулбол"]:
        cb = user['selected_brawler']
        lvl = user['brawlers'][cb]
        
        win_chance = 0.50 + (lvl - 1) * 0.04
        if cb == "Шелли": win_chance += 0.05
        if cb == "Мортис": win_chance -= 0.12
        if cb == "Пайпер": win_chance += (lvl * 0.02)

        if random.random() < win_chance:
            cups_win = 15 if cb == "Мортиis" else 10
            if cb == "Мортис": cups_win = 15
            if cb == "Драко" and message.text == "🌵 Одиночное Столкновение": cups_win = 25
            if cb == "Джесси" and message.text == "⚽ Броулбол": cups_win += 5
            if cb == "Кит" and len(user['friends']) > 0: cups_win *= 2
            
            gold_win = 30
            if cb == "Кольт": gold_win = int(gold_win * 1.20)
            if cb == "Динамайк" and message.text == "🌵 Одиночное Столкновение": gold_win += 50
            if cb == "Гром" and message.text == "⚽ Броулбол": gold_win += 30
            
            xp_win = 40
            if cb == "Брок": xp_win = int(xp_win * 1.25)
            if cb == "Мелоди" and message.text == "⚽ Броулбол": xp_win = int(xp_win * 1.30)
            
            user['cups'] += cups_win; user['coins'] += gold_win; user['pass_xp'] += xp_win; user['wins'] += 1
            res = f"🔥 **ПОБЕДА!**\nЭкипирован боец: {cb}\nНаграды: +{cups_win} 🏆, +{gold_win} 💰, +{xp_win} XP Пасса!"
        else:
            cups_lose = 7
            if cb == "Леон": cups_lose = 2
            if cb == "Мико" and user['cups'] < 300: cups_lose = 0
            if cb == "Гас" and user['cups'] < 150: cups_lose = 0
            user['cups'] = max(0, user['cups'] - cups_lose)
            
            xp_lose_reward = 0
            if cb == "Бо": xp_lose_reward = 5
            user['pass_xp'] += xp_lose_reward
            
            res = f"❌ **ПОРАЖЕНИЕ!**\nПотеряно: -{cups_lose} 🏆."
            if xp_lose_reward > 0: res += f" (Пассивка Бо принесла утешительные +{xp_lose_reward} XP)"

        for q in user['quests']:
            if "Столкновении" in q['desc'] and message.text == "🌵 Одиночное Столкновение": q['done'] = True
        bot.send_message(message.chat.id, res, reply_markup=get_main_markup())

    elif message.text == "👤 Профиль":
        b_list = []
        for b, l in user['brawlers'].items():
            rarity = ALL_BRAWLERS.get(b, {"rarity": "🟢 Редкий"})["rarity"]
            b_list.append(f"• {b} [Сила {l}] — *{rarity}*")
            
        header = THEMES.get(user['bg'], THEMES["Classic Blue"])
        
        inline_up = telebot.types.InlineKeyboardMarkup()
        for b in user['brawlers'].keys():
            inline_up.add(telebot.types.InlineKeyboardButton(text=f"🧪 Апнуть {b} (-{user['brawlers'][b]*400} 💰)", callback_data=f"up_{b}"))

        card = f"{header}\n👤 Аккаунт: {user['name']}\n🎯 Выбранный в бой: **{user['selected_brawler']}**\n🏆 Кубки: {user['cups']} | 💰 Монеты: {user['coins']} | 💎 Гемы: {user['gems']}\n\n🦸‍♂️ Коллекция бравлеров:\n" + "\n".join(b_list)
        bot.send_message(message.chat.id, card, reply_markup=inline_up)

    elif message.text == "✨ Starr Drops":
        inline_starr = telebot.types.InlineKeyboardMarkup()
        inline_starr.add(telebot.types.InlineKeyboardButton("🟡 Открыть Starr Drop 🟡", callback_data="roll_starr_drop"))
        bot.send_message(message.chat.id, "✨ **СИМУЛЯТОР СТАРР ДРОПОВ**\n\nВыбивай золото, гемы и новых эксклюзивных бравлеров мифической или легендарной редкости!", reply_markup=inline_starr)

    elif message.text == "🎁 Награда":
        now = datetime.datetime.now()
        if user['last_daily'] and (now - user['last_daily']).total_seconds() < 86400:
            bot.send_message(message.chat.id, "⏳ Подарок обновится раз в 24 часа.")
        else:
            user['last_daily'] = now
            reward_coins = 400
            if user['selected_brawler'] == "Роза": reward_coins = int(reward_coins * 1.1)
            user['coins'] += reward_coins; user['gems'] += 10
            bot.send_message(message.chat.id, f"🎁 Награда получена! Зачислено: +{reward_coins} Монет, +10 Гемов.")

    elif message.text == "Назад":
        bot.send_message(message.chat.id, "Возврат в главное лобби.", reply_markup=get_main_markup())
        
    else:
        bot.send_message(message.chat.id, "Главный хаб Vasanin Brawl:", reply_markup=get_main_markup())

@app.route('/')
def home(): return "Server OK"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
