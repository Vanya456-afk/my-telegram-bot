import telebot
import os
import random
from flask import Flask
import threading
import datetime

# Инициализация бота и веб-сервера для деплоя
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- ГЛОБАЛЬНАЯ БАЗА ДАННЫХ В ПАМЯТИ ---
players = {}
clans = {}  # Структура: "Название": {'owner': id, 'cups': 0, 'treasury': 0, 'members': [ids], 'requests': [ids], 'boss_hp': 5000}

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
            'friends': []  # Список ID друзей пользователя
        }
    return players[user_id]

user_states = {}

THEMES = {
    "Classic Blue": "🟦 КЛАССИЧЕСКИЙ СИНИЙ ПРОФИЛЬ 🟦",
    "Brawl Ball Stadium": "⚽ СТАДИОН БРОУЛБОЛА ⚽",
    "Wild West": "🌵 ДИКИЙ ЗАПАД 🌵",
    "Golden Arena": "✨ ЗОЛОТАЯ АРЕНА ✨"
}

# --- КЛАВИАТУРЫ ИНТЕРФЕЙСА ---
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

# --- ТОЧКА ВХОДА (КОМАНДА /START + РЕФЕРАЛЫ С ДРУЗЬЯМИ) ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or f"User_{user_id}"
    
    # Парсинг ссылки формата t.me/bot?start=ID для автоматического добавления в друзья
    args = message.text.split()
    user = get_player(user_id, name)
    
    if len(args) > 1:
        try:
            target_id = int(args[1])
            if target_id != user_id and target_id in players:
                if target_id not in user['friends']:
                    user['friends'].append(target_id)
                    players[target_id]['friends'].append(user_id)
                    bot.send_message(target_id, f"🤝 Игрок **{name}** добавил вас в друзья по вашей инвайт-ссылке!")
                    bot.send_message(message.chat.id, f"🎉 Вы добавили игрока **{players[target_id]['name']}** в свой список друзей!")
        except ValueError:
            pass

    bot.send_message(message.chat.id, f"🔥 Добро пожаловать в Vasanin Brawl, {name}!", reply_markup=get_main_markup())

# --- ОБРАБОТКА НАЖАТИЙ ИНЛАЙН-КНОПОК (CALLBACK QUERIES) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_player(user_id)
    
    # 1. Прокачка силы персонажей
    if call.data.startswith("up_"):
        brawler = call.data.replace("up_", "")
        if brawler not in user['brawlers']:
            bot.answer_callback_query(call.id, f"❌ Боец {brawler} еще не разблокирован!", show_alert=True)
            return
        curr_lvl = user['brawlers'][brawler]
        if curr_lvl >= 11:
            bot.answer_callback_query(call.id, f"❌ Достигнут максимальный 11 уровень силы!", show_alert=True)
            return
        cost = curr_lvl * 400
        if user['coins'] < cost:
            bot.answer_callback_query(call.id, f"❌ Недостаточно монет. Стоимость улучшения: {cost} 💰", show_alert=True)
        else:
            user['coins'] -= cost
            user['brawlers'][brawler] += 1
            bot.answer_callback_query(call.id, f"🎉 Сила {brawler} успешно повышена!")
            bot.send_message(call.message.chat.id, f"🧪 Боец **{brawler}** улучшен до **{user['brawlers'][brawler]} уровня силы**!")

    # 2. Одобрение заявок в клан (Модерация)
    elif call.data.startswith("accept_"):
        applicant_id = int(call.data.replace("accept_", ""))
        c_name = user['clan']
        if c_name and c_name in clans and applicant_id in clans[c_name]['requests']:
            clans[c_name]['requests'].remove(applicant_id)
            clans[c_name]['members'].append(applicant_id)
            if applicant_id in players:
                players[applicant_id]['clan'] = c_name
                clans[c_name]['cups'] += players[applicant_id]['cups']
                bot.send_message(applicant_id, f"🎉 Отличные новости! Твоя заявка одобрена, ты вступил в клан **{c_name}**!")
            bot.answer_callback_query(call.id, "✅ Заявка успешно принята!")
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🤝 Игрок принят в команду.")

    # 3. Просмотр карточки профиля друга
    elif call.data.startswith("view_friend_"):
        f_id = int(call.data.replace("view_friend_", ""))
        if f_id not in players:
            bot.answer_callback_query(call.id, "❌ Не удалось загрузить данные игрока.", show_alert=True)
            return
        
        f_user = players[f_id]
        f_brawlers = [f"• {b} [{l} ур]" for b, l in f_user['brawlers'].items()]
        f_clan = f_user['clan'] if f_user['clan'] else "Не состоит в банде"
        
        card = (
            f"👤 **ПРОФИЛЬ ИГРОКА** 👤\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 Никнейм: {f_user['name']}\n"
            f"🏆 Трофеи: {f_user['cups']} 🏆\n"
            f"🛡️ Клан/Банда: **{f_clan}**\n"
            f"📈 Всего побед: {f_user['wins']}\n\n"
            f"🦸‍♂️ Бойцы на аккаунте:\n" + "\n".join(f_brawlers) + "\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        
        inline_m = telebot.types.InlineKeyboardMarkup()
        inline_m.add(telebot.types.InlineKeyboardButton("❌ Удалить из друзей", callback_data=f"remove_friend_{f_id}"))
        bot.send_message(call.message.chat.id, card, reply_markup=inline_m)
        bot.answer_callback_query(call.id)

    # 4. Удаление из списка друзей
    elif call.data.startswith("remove_friend_"):
        f_id = int(call.data.replace("remove_friend_", ""))
        if f_id in user['friends']:
            user['friends'].remove(f_id)
            if user_id in players.get(f_id, {}).get('friends', []):
                players[f_id]['friends'].remove(user_id)
            
            bot.answer_callback_query(call.id, "Пользователь удален из друзей", show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ Связь разорвана. Игрок удален из вашего списка друзей.")

# --- ТЕКСТОВЫЕ МЕХАНИКИ И СТЕЙТЫ ВВОДА ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    user = get_player(user_id, name)

    # Логика обработки активных состояний (States) ввода данных от пользователя
    if user_id in user_states:
        state = user_states[user_id]
        
        # Ввод промокода
        if state == 'promo_input':
            del user_states[user_id]
            code = message.text.strip()
            if code == "АняСамаяЛучшая":
                if "АняСамаяЛучшая" in user['used_promos']:
                    bot.send_message(message.chat.id, "❌ Вы уже активировали данный промокод на этом аккаунте!", reply_markup=get_main_markup())
                else:
                    user['used_promos'].append("АняСамаяЛучшая")
                    user['brawlers']["❄️ Луми"] = 1
                    user['skins'].extend(["«Новогодняя Луми»", "«Кибер-Луми»", "«Королева Луми»"])
                    res = (
                        f"🎁 **АКТИВАЦИЯ ПРОМОКОДА ПРОШЛА УСПЕШНО** 🎁\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🦸‍♂️ Разблокирован Хроматический боец: **❄️ Луми**\n"
                        f"👕 Добавлен эксклюзивный гардероб скинов:\n"
                        f"• Скин: «Новогодняя Луми»\n"
                        f"• Скин: «Кибер-Луми»\n"
                        f"• Скин: «Королева Луми»\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"✨ Все награды успешно зачислены!"
                    )
                    bot.send_message(message.chat.id, res, reply_markup=get_main_markup())
            else:
                bot.send_message(message.chat.id, "❌ Указанный промокод недействителен или устарел.", reply_markup=get_main_markup())
            return

        # Ставка в костях (Казино Старр)
        elif state == 'dice_bet':
            del user_states[user_id]
            try:
                bet = int(message.text)
                if bet <= 0 or user['coins'] < bet: raise ValueError
                
                user['coins'] -= bet
                player_score = random.randint(1, 6)
                bot_score = random.randint(1, 6)
                
                # Засчитываем квест, если есть задача на кубики
                for q in user['quests']:
                    if "кубиках" in q['desc']: q['done'] = True
                
                res = f"🎲 **ДУЭЛЬ НА КУБИКАХ (КАЗИНО СТАРР)** 🎲\n\n👤 Твой бросок: **{player_score}**\n🤖 Бросок Дилера Казино: **{bot_score}**\n\n"
                if player_score > bot_score:
                    win = bet * 2
                    user['coins'] += win
                    res += f"🎉 **ПОБЕДА!** Вы обыграли дилера и забрали: +{win} монет!"
                elif player_score < bot_score:
                    res += f"❌ **ПРОИГРЫШ!** Твоя ставка в размере {bet} монет уходит в банк казино."
                else:
                    user['coins'] += bet
                    res += f"🤝 **НИЧЬЯ!** Очки равны. Полная ставка {bet} монет возвращена на баланс."
                bot.send_message(message.chat.id, res, reply_markup=get_main_markup())
            except ValueError:
                bot.send_message(message.chat.id, "❌ Некорректная ставка или недостаточно монет на балансе.", reply_markup=get_main_markup())
            return

        # Создание клана
        elif state == 'clan_create':
            del user_states[user_id]
            c_name = message.text.strip()
            if c_name in clans or len(c_name) < 3:
                bot.send_message(message.chat.id, "❌ Название уже занято бандами или слишком короткое.", reply_markup=get_main_markup())
                return
            user['coins'] -= 1000
            user['clan'] = c_name
            clans[c_name] = {'owner': user_id, 'cups': user['cups'], 'treasury': 0, 'members': [user_id], 'requests': [], 'boss_hp': 5000}
            bot.send_message(message.chat.id, f"🛡️ Клан **{c_name}** официально зарегистрирован в реестре!", reply_markup=get_clan_markup(True))
            return

        # Взнос монет в казну клана
        elif state == 'clan_deposit':
            del user_states[user_id]
            try:
                dep = int(message.text)
                if dep <= 0 or user['coins'] < dep: raise ValueError
                user['coins'] -= dep
                if user['clan'] in clans:
                    clans[user['clan']]['treasury'] += dep
                    bot.send_message(message.chat.id, f"💰 Успешный перевод! Вы внесли в казну банды {dep} монет!", reply_markup=get_clan_markup(True))
            except ValueError:
                bot.send_message(message.chat.id, "❌ Неверно указана сумма взноса.", reply_markup=get_clan_markup(True))
            return

        # Ставка на Brawl TV
        elif state.startswith('bet_amt_'):
            del user_states[user_id]
            chosen_bot = state.replace('bet_amt_', '')
            try:
                amount = int(message.text)
                if amount <= 0 or user['coins'] < amount: raise ValueError
                user['coins'] -= amount
                winner = random.choice(["Эль Примо", "Поко"])
                for q in user['quests']:
                    if "Brawl TV" in q['desc']: q['done'] = True
                if winner == chosen_bot:
                    win_cash = int(amount * 1.95)
                    user['coins'] += win_cash
                    res = f"📺 **Brawl TV LIVE**\n\n🔥 Твой фаворит **{chosen_bot}** одержал победу!\n💰 Выигрыш со ставки: +{win_cash} монет!"
                else:
                    res = f"📺 **Brawl TV LIVE**\n\n❌ {chosen_bot} потерпел поражение от {winner}. Ставка сгорела."
                bot.send_message(message.chat.id, res, reply_markup=get_main_markup())
            except ValueError:
                bot.send_message(message.chat.id, "❌ Ошибка транзакции.", reply_markup=get_main_markup())
            return

    # --- МЕНЮ СООБЩЕСТВА & СИСТЕМА ДРУЗЕЙ ---
    if message.text == "👥 Сообщество":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add("📜 Мои Друзья", "🔗 Получить инвайт-ссылку", "Назад")
        bot.send_message(message.chat.id, "👥 Меню взаимодействия сообщества Vasanin Brawl. Выберите вкладку:", reply_markup=markup)

    elif message.text == "🔗 Получить инвайт-ссылку":
        bot_info = bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(message.chat.id, f"🔗 **Твоя инвайт-ссылка для добавления друзей:**\n`{invite_link}`\n\nСкопируй её и отправь товарищу. При её активации вы мгновенно станете друзьями в игре!")

    elif message.text == "📜 Мои Друзья":
        if not user['friends']:
            bot.send_message(message.chat.id, "📜 Твой список друзей пуст. Отправь инвайт-ссылку знакомым!", reply_markup=get_main_markup())
            return
        
        bot.send_message(message.chat.id, f"👥 **СПИСОК ТВОИХ ДРУЗЕЙ ({len(user['friends'])}):**")
        for f_id in user['friends']:
            f_data = players.get(f_id, {'name': f"User_{f_id}", 'cups': 0})
            inline_f = telebot.types.InlineKeyboardMarkup()
            inline_f.add(telebot.types.InlineKeyboardButton("🔎 Посмотреть профиль", callback_data=f"view_friend_{f_id}"))
            bot.send_message(message.chat.id, f"👤 **{f_data['name']}** — {f_data['cups']} 🏆", reply_markup=inline_f)

    # --- КАЗИНО НА КУБИКАХ ---
    elif message.text == "🎲 Казино Старр":
        user_states[user_id] = 'dice_bet'
        bot.send_message(message.chat.id, f"🎲 Добро пожаловать в игру в кости Казино Старр!\nТвой баланс: {user['coins']} 💰\n\nВведите сумму ставки на раунд против дилера:")

    # --- ПРОМОКОДЫ ---
    elif message.text == "🎫 Промокоды":
        user_states[user_id] = 'promo_input'
        bot.send_message(message.chat.id, "🎫 Введите действующий буквенный промокод для получения наград:")

    # --- СИСТЕМА КЛАНОВ ---
    elif message.text == "🛡️ Кланы":
        has_clan = user['clan'] is not None
        bot.send_message(message.chat.id, f"🛡️ **Клановый Центр Управления**\nТекущая банда: {user['clan'] if has_clan else 'Вы не состоите в клане'}", reply_markup=get_clan_markup(has_clan))

    elif message.text == "🆕 Создать Клан (1000 💰)":
        if user['coins'] < 1000:
            bot.send_message(message.chat.id, "❌ Недостаточно золота для регистрации синдиката!", reply_markup=get_main_markup())
            return
        user_states[user_id] = 'clan_create'
        bot.send_message(message.chat.id, "Введите уникальное название для новой банды:")

    elif message.text == "🔍 Случайный клан":
        if not clans:
            bot.send_message(message.chat.id, "❌ На сервере пока не создано ни одного клана.", reply_markup=get_main_markup())
        else:
            c_name = random.choice(list(clans.keys()))
            if user_id not in clans[c_name]['members'] and user_id not in clans[c_name]['requests']:
                clans[c_name]['requests'].append(user_id)
                bot.send_message(message.chat.id, f"📩 Заявка на вступление в клан **{c_name}** отправлена лидерам банды!")

    elif message.text == "👥 Участники клана":
        c_name = user['clan']
        if c_name and c_name in clans:
            m_list = []
            for uid in clans[c_name]['members']:
                uname = players.get(uid, {}).get('name', f"User_{uid}")
                cups = players.get(uid, {}).get('cups', 0)
                role = "👑 Глава" if uid == clans[c_name]['owner'] else "⚔️ Рейдер"
                m_list.append(f"• {uname} ({cups} 🏆) — {role}")
            bot.send_message(message.chat.id, f"👥 **Состав синдиката {c_name}**:\n\n" + "\n".join(m_list))

    elif message.text == "📩 Заявки на вход":
        c_name = user['clan']
        if c_name and c_name in clans:
            if clans[c_name]['owner'] != user_id:
                bot.send_message(message.chat.id, "❌ Управление заявками доступно только создателю клана!")
                return
            if not clans[c_name]['requests']:
                bot.send_message(message.chat.id, "📩 Список входящих заявок пуст.")
                return
            for req_id in clans[c_name]['requests']:
                req_name = players.get(req_id, {}).get('name', f"User_{req_id}")
                req_cups = players.get(req_id, {}).get('cups', 0)
                inline_m = telebot.types.InlineKeyboardMarkup()
                inline_m.add(telebot.types.InlineKeyboardButton("✅ Принять в клан", callback_data=f"accept_{req_id}"))
                bot.send_message(message.chat.id, f"Заявка на вход от: **{req_name}** ({req_cups} 🏆)", reply_markup=inline_m)

    elif message.text == "💰 Внести в казну":
        user_states[user_id] = 'clan_deposit'
        bot.send_message(message.chat.id, "Укажите количество монет для отправки в общую казну:")

    elif message.text == "📊 Статистика клана":
        c_name = user['clan']
        if c_name and c_name in clans:
            c = clans[c_name]
            bot.send_message(message.chat.id, f"🛡️ **Клан {c_name}**\n🏆 Суммарные трофеи: {c['cups']}\n💰 Баланс казны: {c['treasury']} монет\n👥 Бойцов в банде: {len(c['members'])}\n🤖 Здоровье Робо-Босса: {c['boss_hp']}/5000")

    elif message.text == "⚔️ Рейд на Робо-Босса":
        c_name = user['clan']
        if not c_name or c_name not in clans: return
        now = datetime.datetime.now()
        if user['last_boss_attack'] and (now - user['last_boss_attack']).total_seconds() < 3600:
            bot.send_message(message.chat.id, "⏳ Твоя команда восстанавливает силы. Набеги доступны раз в 60 минут!")
            return
        user['last_boss_attack'] = now
        dmg = random.randint(450, 1100)
        clans[c_name]['boss_hp'] = max(0, clans[c_name]['boss_hp'] - dmg)
        user['coins'] += 250
        bot.send_message(message.chat.id, f"💥 Бум! Вы нанесли Боссу **{dmg} урона**! Клан гордится вами. Награда: +250 💰.", reply_markup=get_clan_markup(True))

    elif message.text == "🚪 Покинуть клан":
        c_name = user['clan']
        if c_name and c_name in clans:
            clans[c_name]['members'].remove(user_id)
            user['clan'] = None
            bot.send_message(message.chat.id, "Вы вышли из состава банды.", reply_markup=get_main_markup())

    # --- ИГРОВОЙ ПРОЦЕСС (МАТЧМЕЙКИНГ) ---
    elif message.text == "⚔️ В бой!":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🌵 Столкновение", "⚽ Броулбол", "💎 Захват Кристаллов", "Назад")
        bot.send_message(message.chat.id, "Выберите игровой режим:", reply_markup=markup)

    elif message.text in ["🌵 Столкновение", "⚽ Броулбол", "💎 Захват Кристаллов"]:
        current_brawler = random.choice(list(user['brawlers'].keys()))
        lvl = user['brawlers'][current_brawler]
        # Шанс победы зависит от уровня силы персонажа
        if random.random() < (0.50 + (lvl - 1) * 0.04):
            user['cups'] += 10; user['coins'] += 30; user['wins'] += 1; user['pass_xp'] += 30
            if user['clan'] in clans: clans[user['clan']]['cups'] += 10
            res = f"✅ **ПОБЕДА!** Режим пройден персонажем {current_brawler}! Награды: +10 🏆, +30 💰, +30 XP Vasanin Pass!"
        else:
            user['cups'] = max(0, user['cups'] - 7); user['pass_xp'] += 10
            res = f"❌ **ПОРАЖЕНИЕ!** Вы уступили кубки вражеской команде: -7 🏆. Получено +10 XP утешительных."
        bot.send_message(message.chat.id, res, reply_markup=get_main_markup())

    # --- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ---
    elif message.text == "👤 Профиль":
        b_list = [f"• {b} [Сила {l}]" for b, l in user['brawlers'].items()]
        header = THEMES.get(user['bg'], THEMES["Classic Blue"])
        card = f"{header}\n👤 Игрок: {user['name']}\n🏆 Кубки: {user['cups']} | 💰 Монеты: {user['coins']} | 💎 Гемы: {user['gems']}\n\n🦸‍♂️ Ваша команда бойцов:\n" + "\n".join(b_list)
        bot.send_message(message.chat.id, card, reply_markup=get_brawlers_inline_markup())

    # --- СИМУЛЯЦИЯ СТАВОК BRAWL TV ---
    elif message.text == "📺 Brawl TV":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🔥 На Эль Примо", "🔥 На Поко", "Назад")
        bot.send_message(message.chat.id, "📺 Прямой эфир киберспорта. Выберите бойца, на которого хотите заключить пари:", reply_markup=markup)

    elif message.text in ["🔥 На Эль Примо", "🔥 На Поко"]:
        b_n = "Эль Примо" if "Примо" in message.text else "Поко"
        user_states[user_id] = f'bet_amt_{b_n}'
        bot.send_message(message.chat.id, f"Введите сумму монет для ставки на победу {b_n}:")

    # --- КВЕСТЫ ---
    elif message.text == "📜 Квесты":
        q_text = ["📜 **Текущие боевые задачи:**\n"]
        for q in user['quests']:
            status = "✅ Выполнено" if q['done'] else "⏳ В процессе"
            q_text.append(f"• {q['desc']} — {status}")
        bot.send_message(message.chat.id, "\n".join(q_text))

    # --- ЕЖЕДНЕВНЫЙ ПОДАРOК ---
    elif message.text == "🎁 Награда":
        now = datetime.datetime.now()
        if user['last_daily'] and (now - user['last_daily']).total_seconds() < 86400:
            bot.send_message(message.chat.id, "⏳ Приходите завтра! Ежедневная награда еще перезаряжается.")
        else:
            user['last_daily'] = now; user['coins'] += 500
            bot.send_message(message.chat.id, "🎁 Поздравляем! Получен бесплатный ежедневный подарок: +500 💰 монет!")

    # --- СИСТЕМНЫЙ НАВИГАТОР НАЗАД ---
    elif message.text == "Назад":
        bot.send_message(message.chat.id, "Возвращаю вас в главное меню:", reply_markup=get_main_markup())

@app.route('/')
def home(): 
    return "Server Alive"

if __name__ == "__main__":
    # Запуск бота в отдельном потоке polling, чтобы Flask не блокировал выполнение
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
