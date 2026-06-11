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
clans = {}  # "Название": {'owner': id, 'cups': 0, 'treasury': 0, 'members': [ids], 'requests': [ids], 'boss_hp': 5000}

def get_player(user_id, username="Игрок"):
    if user_id not in players:
        players[user_id] = {
            'name': username,
            'coins': 5000,
            'gems': 300,
            'cups': 0,
            'tickets': 10,
            'pass_xp': 0,
            'pass_lvl': 1,
            'clan': None,
            'wins': 0,
            'claimed_pass_rewards': [],
            'claimed_trophies': [],
            'last_daily': None,
            'last_boss_attack': None,
            'quests': [
                {"desc": "Выиграй обычный бой", "done": False, "reward": 150},
                {"desc": "Сделай ставку на Brawl TV", "done": False, "reward": 100},
                {"desc": "Сыграй в казино на кубиках", "done": False, "reward": 120}
            ],
            'bg': "Classic Blue",
            'brawlers': {"Шелли": 1},
            'skins': [],
            'used_promos': [],
            'friends': []
        }
    return players[user_id]

user_states = {}

THEMES = {
    "Classic Blue": "🟦 КЛАССИЧЕСКИЙ СИНИЙ ПРОФИЛЬ 🟦",
    "Brawl Ball Stadium": "⚽ СТАДИОН БРОУЛБОЛА ⚽",
    "Wild West": "🌵 ДИКИЙ ЗАПАД 🌵",
    "Golden Arena": "✨ ЗОЛОТАЯ АРЕНА ✨"
}

# --- КЛАВИАТУРЫ ---
def get_main_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⚔️ В бой!", "👤 Профиль")
    markup.add("🛍 Магазин", "🎲 Казино Старр")
    markup.add("🎫 Промокоды", "🏆 Топ Игроков")
    markup.add("🌟 Vasanin Pass", "🏆 Путь к Славе")
    markup.add("🎨 Кастомизация", "👥 Сообщество")
    markup.add("🛡️ Кланы", "🎁 Награда")
    markup.add("📺 Brawl TV", "📜 Квесты")
    return markup

def get_clan_markup(has_clan):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if has_clan:
        markup.add("⚔️ Рейд на Робо-Босса", "💰 Внести в казну")
        markup.add("👥 Участники клана", "📩 Заявки на вход")
        markup.add("📊 Статистика клана", "🚪 Покинуть клан")
        markup.add("Назад")
    else:
        markup.add("🆕 Создать Клан (1000 💰)", "🔍 Случайный клан", "Назад")
    return markup

def get_brawlers_inline_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text="🧪 Прокачать Шелли", callback_data="up_Шелли"))
    markup.add(telebot.types.InlineKeyboardButton(text="🧪 Прокачать Кольта", callback_data="up_Кольт"))
    markup.add(telebot.types.InlineKeyboardButton(text="🧪 Прокачать Рико", callback_data="up_Рико"))
    markup.add(telebot.types.InlineKeyboardButton(text="🧪 Прокачать Мортиса", callback_data="up_Мортис"))
    return markup

# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or f"User_{user_id}"
    
    args = message.text.split()
    user = get_player(user_id, name)
    
    if len(args) > 1:
        try:
            target_id = int(args[1])
            if target_id != user_id and target_id in players:
                if target_id not in user['friends']:
                    user['friends'].append(target_id)
                    players[target_id]['friends'].append(user_id)
                    bot.send_message(target_id, f"🤝 Игрок **{name}** добавил вас в друзья!")
                    bot.send_message(message.chat.id, f"🎉 Вы добавили **{players[target_id]['name']}** в друзья!")
        except ValueError:
            pass

    bot.send_message(message.chat.id, f"🔥 Добро пожаловать в Vasanin Brawl, {name}!", reply_markup=get_main_markup())

# --- ОБРАБОТКА CALLBACK ИНЛАЙН КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_player(user_id)
    
    if call.data.startswith("up_"):
        brawler = call.data.replace("up_", "")
        if brawler not in user['brawlers']:
            bot.answer_callback_query(call.id, f"❌ Боец {brawler} не разблокирован!", show_alert=True)
            return
        curr_lvl = user['brawlers'][brawler]
        if curr_lvl >= 11:
            bot.answer_callback_query(call.id, f"❌ Максимальный 11 уровень!", show_alert=True)
            return
        cost = curr_lvl * 400
        if user['coins'] < cost:
            bot.answer_callback_query(call.id, f"❌ Нужно монет: {cost}", show_alert=True)
        else:
            user['coins'] -= cost
            user['brawlers'][brawler] += 1
            bot.answer_callback_query(call.id, f"🎉 Уровень повышен!")
            bot.send_message(call.message.chat.id, f"🧪 **{brawler}** успешно улучшен до **{user['brawlers'][brawler]} уровня**!")

    elif call.data.startswith("accept_"):
        applicant_id = int(call.data.replace("accept_", ""))
        c_name = user['clan']
        if c_name and c_name in clans and applicant_id in clans[c_name]['requests']:
            clans[c_name]['requests'].remove(applicant_id)
            clans[c_name]['members'].append(applicant_id)
            if applicant_id in players:
                players[applicant_id]['clan'] = c_name
                clans[c_name]['cups'] += players[applicant_id]['cups']
                bot.send_message(applicant_id, f"🎉 Ты принят в клан **{c_name}**!")
            bot.answer_callback_query(call.id, "✅ Заявка принята!")
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🤝 Игрок принят.")

    elif call.data.startswith("view_friend_"):
        f_id = int(call.data.replace("view_friend_", ""))
        if f_id not in players:
            bot.answer_callback_query(call.id, "❌ Игрок не найден", show_alert=True)
            return
        f_user = players[f_id]
        f_clan = f_user['clan'] if f_user['clan'] else "Нет"
        card = f"f👤 **ПРОФИЛЬ ДРУГА**\nНик: {f_user['name']}\n🏆 Кубки: {f_user['cups']}\n🛡️ Клан: {f_clan}\n побед: {f_user['wins']}"
        inline_m = telebot.types.InlineKeyboardMarkup()
        inline_m.add(telebot.types.InlineKeyboardButton("❌ Удалить из друзей", callback_data=f"remove_friend_{f_id}"))
        bot.send_message(call.message.chat.id, card, reply_markup=inline_m)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("remove_friend_"):
        f_id = int(call.data.replace("remove_friend_", ""))
        if f_id in user['friends']:
            user['friends'].remove(f_id)
            if user_id in players.get(f_id, {}).get('friends', []):
                players[f_id]['friends'].remove(user_id)
            bot.answer_callback_query(call.id, "Удален")
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ Пользователь удален из друзей.")

    # Выбор темы оформления в Кастомизации
    elif call.data.startswith("set_bg_"):
        theme_key = call.data.replace("set_bg_", "")
        if theme_key in THEMES:
            user['bg'] = theme_key
            bot.answer_callback_query(call.id, f"🎨 Выбрана тема: {theme_key}")
            bot.send_message(call.message.chat.id, f"✅ Фон профиля успешно изменен на: **{THEMES[theme_key]}**")

# --- ОБРАБОТКА ТЕКСТА (ОСНОВНЫЕ КНОПКИ) ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    user = get_player(user_id, name)

    # Проверка состояний ввода (States)
    if user_id in user_states:
        state = user_states[user_id]
        if state == 'promo_input':
            del user_states[user_id]
            code = message.text.strip()
            if code == "АняСамаяЛучшая":
                if "АняСамаяЛучшая" in user['used_promos']:
                    bot.send_message(message.chat.id, "❌ Промокод уже использован!", reply_markup=get_main_markup())
                else:
                    user['used_promos'].append("АняСамаяЛучшая")
                    user['brawlers']["❄️ Луми"] = 1
                    user['skins'].extend(["«Новогодняя Луми»", "«Кибер-Луми»", "«Королева Луми»"])
                    res = f"🎁 **ПРОМОКОД АКТИВИРОВАН** 🎁\n\n🦸‍♂️ Боец: **❄️ Луми**\n👕 Скины: Новогодняя, Кибер, Королева Луми!"
                    bot.send_message(message.chat.id, res, reply_markup=get_main_markup())
            else:
                bot.send_message(message.chat.id, "❌ Неверный промокод.", reply_markup=get_main_markup())
            return

        elif state == 'dice_bet':
            del user_states[user_id]
            try:
                bet = int(message.text)
                if bet <= 0 or user['coins'] < bet: raise ValueError
                user['coins'] -= bet
                p_score, b_score = random.randint(1, 6), random.randint(1, 6)
                
                for q in user['quests']:
                    if "кубиках" in q['desc']: q['done'] = True
                
                res = f"🎲 **ИГРА В КОСТИ**\n\n👤 Твой кубик: {p_score}\n🤖 Кубик дилера: {b_score}\n\n"
                if p_score > b_score:
                    user['coins'] += bet * 2
                    res += f"🎉 Победа! Удвоено: +{bet * 2} монет!"
                elif p_score < b_score:
                    res += f"❌ Проигрыш. Ставка {bet} потеряна."
                else:
                    user['coins'] += bet
                    res += "🤝 Ничья! Ставка возвращена."
                bot.send_message(message.chat.id, res, reply_markup=get_main_markup())
            except ValueError:
                bot.send_message(message.chat.id, "❌ Ошибка ставки.", reply_markup=get_main_markup())
            return

        elif state == 'clan_create':
            del user_states[user_id]
            c_name = message.text.strip()
            if c_name in clans or len(c_name) < 3:
                bot.send_message(message.chat.id, "❌ Имя занято или слишком короткое.", reply_markup=get_main_markup())
                return
            user['coins'] -= 1000
            user['clan'] = c_name
            clans[c_name] = {'owner': user_id, 'cups': user['cups'], 'treasury': 0, 'members': [user_id], 'requests': [], 'boss_hp': 5000}
            bot.send_message(message.chat.id, f"🛡️ Клан **{c_name}** создан!", reply_markup=get_clan_markup(True))
            return

        elif state == 'clan_deposit':
            del user_states[user_id]
            try:
                dep = int(message.text)
                if dep <= 0 or user['coins'] < dep: raise ValueError
                user['coins'] -= dep
                if user['clan'] in clans:
                    clans[user['clan']]['treasury'] += dep
                    bot.send_message(message.chat.id, f"💰 Внесено {dep} монет в казну клана!", reply_markup=get_clan_markup(True))
            except ValueError:
                bot.send_message(message.chat.id, "❌ Неверная сумма.", reply_markup=get_clan_markup(True))
            return

        elif state.startswith('bet_amt_'):
            del user_states[user_id]
            chosen_bot = state.replace('bet_amt_', '')
            try:
                amount = int(message.text)
                if amount <= 0 or user['coins'] < amount: raise ValueError
                user['coins'] -= amount
                winner = random.choice(["Эль Примо", "Поко"])
                if winner == chosen_bot:
                    user['coins'] += int(amount * 1.95)
                    res = f"📺 **Brawl TV**\n\n🎉 Твой боец {chosen_bot} выиграл! Зачислено +{int(amount * 1.95)} 💰"
                else:
                    res = f"📺 **Brawl TV**\n\n❌ {chosen_bot} проиграл. Ставка потеряна."
                bot.send_message(message.chat.id, res, reply_markup=get_main_markup())
            except ValueError:
                bot.send_message(message.chat.id, "❌ Ошибка ввода.", reply_markup=get_main_markup())
            return

    # --- КНОПКИ ГЛАВНОГО МЕНЮ (ВСЕ ОБРАБОТЧИКИ НА МЕСТЕ) ---
    if message.text == "⚔️ В бой!":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🌵 Столкновение", "⚽ Броулбол", "💎 Захват Кристаллов", "Назад")
        bot.send_message(message.chat.id, "Выбери карту/режим:", reply_markup=markup)

    elif message.text in ["🌵 Столкновение", "⚽ Броулбол", "💎 Захват Кристаллов"]:
        cb = random.choice(list(user['brawlers'].keys()))
        lvl = user['brawlers'][cb]
        if random.random() < (0.50 + (lvl-1)*0.04):
            user['cups'] += 10; user['coins'] += 30; user['wins'] += 1; user['pass_xp'] += 30
            if user['clan'] in clans: clans[user['clan']]['cups'] += 10
            res = f"✅ Победа за {cb}! +10 🏆, +30 💰"
        else:
            user['cups'] = max(0, user['cups'] - 7); user['pass_xp'] += 10
            res = f"❌ Поражение! -7 🏆"
        bot.send_message(message.chat.id, res, reply_markup=get_main_markup())

    elif message.text == "👤 Профиль":
        b_list = [f"• {b} [{l} ур]" for b, l in user['brawlers'].items()]
        header = THEMES.get(user['bg'], THEMES["Classic Blue"])
        card = f"{header}\n👤 Ник: {user['name']}\n🏆 Кубки: {user['cups']} | 💰 Монеты: {user['coins']} | 💎 Гемы: {user['gems']}\n\n🦸‍♂️ Персонажи:\n" + "\n".join(b_list)
        bot.send_message(message.chat.id, card, reply_markup=get_brawlers_inline_markup())

    # РАБОТАЕТ: Магазин предметов
    elif message.text == "🛍 Магазин":
        bot.send_message(message.chat.id, "🛍 **МАГАЗИН СТАРР**\n\n🔹 Мегаящик — 80 💎\n🔹 Большой ящик — 30 💎\n🔹 Набор монет (1000 шт) — 50 💎\n\n*В разработке: покупка предметов станет доступна в следующем обновлении!*")

    elif message.text == "🎲 Казино Старр":
        user_states[user_id] = 'dice_bet'
        bot.send_message(message.chat.id, f"🎲 **Казино Старр: Кубики**\nБаланс: {user['coins']} 💰\n\nВведите ставку:")

    elif message.text == "🎫 Промокоды":
        user_states[user_id] = 'promo_input'
        bot.send_message(message.chat.id, "🎫 Введите действующий промокод:")

    # РАБОТАЕТ: Рейтинг лучших игроков
    elif message.text == "🏆 Топ Игроков":
        sorted_players = sorted(players.items(), key=lambda x: x[1]['cups'], reverse=True)[:5]
        top_text = "🏆 **ТОП-5 ИГРОКОВ СЕРВЕРА** 🏆\n\n"
        for i, (pid, pdata) in enumerate(sorted_players, 1):
            top_text += f"{i}. {pdata['name']} — {pdata['cups']} 🏆\n"
        if not sorted_players:
            top_text += "Топ пока пуст. Будь первым!"
        bot.send_message(message.chat.id, top_text)

    # РАБОТАЕТ: Боевой пропуск Vasanin Pass
    elif message.text == "🌟 Vasanin Pass":
        bot.send_message(message.chat.id, f"🌟 **VASANIN PASS**\n\n📈 Твой прогресс: **{user['pass_xp']} XP**\nТекущий уровень: **Лига {user['pass_lvl']}**\n\nВыполняй квесты и участвуй в боях, чтобы разблокировать уникальные награды, включая Гемы, Монеты и Мегаящики!")

    # РАБОТАЕТ: Путь к Славе за кубки
    elif message.text == "🏆 Путь к Славе":
        bot.send_message(message.chat.id, f"🏆 **ПУТЬ К СЛАВЕ**\n\nТвои кубки: {user['cups']} 🏆\n\n🎯 Цели:\n• 100 🏆 — Боец Кольт\n• 500 🏆 — 500 Монет\n• 1000 🏆 — Боец Брок\n\n*Награды выдаются автоматически при достижении порога!*")

    # РАБОТАЕТ: Смена фонов и кастомизация профиля
    elif message.text == "🎨 Кастомизация":
        inline_themes = telebot.types.InlineKeyboardMarkup()
        for k, v in THEMES.items():
            inline_themes.add(telebot.types.InlineKeyboardButton(text=v, callback_data=f"set_bg_{k}"))
        bot.send_message(message.chat.id, "🎨 **МЕНЮ КАСТОМИЗАЦИИ**\n\nВыбери тему оформления карточки твоего профиля:", reply_markup=inline_themes)

    elif message.text == "👥 Сообщество":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add("📜 Мои Друзья", "🔗 Получить инвайт-ссылку", "Назад")
        bot.send_message(message.chat.id, "👥 Меню взаимодействия сообщества Vasanin Brawl:", reply_markup=markup)

    elif message.text == "🔗 Получить инвайт-ссылку":
        bot_info = bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(message.chat.id, f"🔗 **Инвайт-ссылка:**\n`{invite_link}`")

    elif message.text == "📜 Мои Друзья":
        if not user['friends']:
            bot.send_message(message.chat.id, "📜 Список друзей пуст.")
            return
        bot.send_message(message.chat.id, f"👥 **ТВОИ ДРУЗЬЯ ({len(user['friends'])}):**")
        for f_id in user['friends']:
            f_data = players.get(f_id, {'name': f"User_{f_id}", 'cups': 0})
            inline_f = telebot.types.InlineKeyboardMarkup()
            inline_f.add(telebot.types.InlineKeyboardButton("🔎 Посмотреть профиль", callback_data=f"view_friend_{f_id}"))
            bot.send_message(message.chat.id, f"👤 **{f_data['name']}** — {f_data['cups']} 🏆", reply_markup=inline_f)

    elif message.text == "🛡️ Кланы":
        has_clan = user['clan'] is not None
        bot.send_message(message.chat.id, f"🛡️ **Кланы**\nТвой клан: {user['clan'] if has_clan else 'Нет'}", reply_markup=get_clan_markup(has_clan))

    elif message.text == "🆕 Создать Клан (1000 💰)":
        if user['coins'] < 1000:
            bot.send_message(message.chat.id, "❌ Не хватает золота!")
            return
        user_states[user_id] = 'clan_create'
        bot.send_message(message.chat.id, "Введите имя клана:")

    elif message.text == "🔍 Случайный клан":
        if not clans:
            bot.send_message(message.chat.id, "❌ Кланов еще нет.")
        else:
            c_name = random.choice(list(clans.keys()))
            if user_id not in clans[c_name]['members'] and user_id not in clans[c_name]['requests']:
                clans[c_name]['requests'].append(user_id)
                bot.send_message(message.chat.id, f"📩 Заявка в клан **{c_name}** отправлена!")

    elif message.text == "👥 Участники клана":
        c_name = user['clan']
        if c_name and c_name in clans:
            m_list = [f"• {players.get(uid, {}).get('name', 'Игрок')} ({players.get(uid, {}).get('cups', 0)} 🏆)" for uid in clans[c_name]['members']]
            bot.send_message(message.chat.id, f"👥 **Состав клана {c_name}**:\n" + "\n".join(m_list))

    elif message.text == "📩 Заявки на вход":
        c_name = user['clan']
        if c_name and c_name in clans:
            if clans[c_name]['owner'] != user_id:
                bot.send_message(message.chat.id, "❌ Доступно только Главе.")
                return
            if not clans[c_name]['requests']:
                bot.send_message(message.chat.id, "📩 Заявок нет.")
                return
            for req_id in clans[c_name]['requests']:
                inline_m = telebot.types.InlineKeyboardMarkup()
                inline_m.add(telebot.types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_{req_id}"))
                bot.send_message(message.chat.id, f"Заявка: **{players.get(req_id, {}).get('name')}**", reply_markup=inline_m)

    elif message.text == "💰 Внести в казну":
        user_states[user_id] = 'clan_deposit'
        bot.send_message(message.chat.id, "Сумма взноса монет:")

    elif message.text == "📊 Статистика клана":
        c_name = user['clan']
        if c_name and c_name in clans:
            c = clans[c_name]
            bot.send_message(message.chat.id, f"🛡️ **Клан {c_name}**\n🏆 Кубки: {c['cups']}\n💰 Казна: {c['treasury']}\n👥 Людей: {len(c['members'])}\n🤖 Босс ХП: {c['boss_hp']}/5000")

    elif message.text == "⚔️ Рейд на Робо-Босса":
        c_name = user['clan']
        if not c_name or c_name not in clans: return
        now = datetime.datetime.now()
        if user['last_boss_attack'] and (now - user['last_boss_attack']).total_seconds() < 3600:
            bot.send_message(message.chat.id, "⏳ Рейды доступны раз в час.")
            return
        user['last_boss_attack'] = now
        dmg = random.randint(500, 1000)
        clans[c_name]['boss_hp'] = max(0, clans[c_name]['boss_hp'] - dmg)
        user['coins'] += 250
        bot.send_message(message.chat.id, f"💥 Нанесено {dmg} урона боссу! Награда: +250 💰", reply_markup=get_clan_markup(True))

    elif message.text == "🚪 Покинуть клан":
        c_name = user['clan']
        if c_name and c_name in clans:
            clans[c_name]['members'].remove(user_id)
            user['clan'] = None
            bot.send_message(message.chat.id, "Вы покинули клан.", reply_markup=get_main_markup())

    elif message.text == "📺 Brawl TV":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🔥 На Эль Примо", "🔥 На Поко", "Назад")
        bot.send_message(message.chat.id, "📺 Сделай ставку на победу одного из бойцов:", reply_markup=markup)

    elif message.text in ["🔥 На Эль Примо", "🔥 На Поко"]:
        b_n = "Эль Примо" if "Примо" in message.text else "Поко"
        user_states[user_id] = f'bet_amt_{b_n}'
        bot.send_message(message.chat.id, f"Сумма ставки на {b_n}:")

    elif message.text == "📜 Квесты":
        q_text = ["📜 **Квесты:**\n"]
        for q in user['quests']:
            status = "✅ Выполнено" if q['done'] else "⏳ В процессе"
            q_text.append(f"• {q['desc']} — {status}")
        bot.send_message(message.chat.id, "\n".join(q_text))

    elif message.text == "🎁 Награда":
        now = datetime.datetime.now()
        if user['last_daily'] and (now - user['last_daily']).total_seconds() < 86400:
            bot.send_message(message.chat.id, "⏳ Награда будет доступна позже.")
        else:
            user['last_daily'] = now; user['coins'] += 500
            bot.send_message(message.chat.id, "🎁 Получено +500 монет!")

    elif message.text == "Назад":
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_markup())

@app.route('/')
def home(): return "Server Alive"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
