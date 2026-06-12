import telebot
import os
import random
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ❗ ГЛАВНЫЙ АДМИН (Создатель): Обязательно замени эти цифры на свой настоящий Telegram ID
CREATOR_ID = 123456789 

# Список всех администраторов (изначально в нем только создатель)
ADMINS = [CREATOR_ID]

players = {}
clans = {}

ALL_BRAWLERS = {
    "Шелли": {"rarity": "🟢 Редкий", "bonus": "Стабильность (+5% к шансу победы)"},
    "Кольт": {"rarity": "🟢 Редкий", "bonus": "Шоумен (+20% к золоту за победы)"},
    "Булл": {"rarity": "🟢 Редкий", "bonus": "Танк (+35% урона по Робо-Боссу)"},
    "Эль Примо": {"rarity": "🟢 Редкий", "bonus": "Гроза кубиков (+20% в Казино)"},
    "Брок": {"rarity": "🔵 Сверхредкий", "bonus": "Ракетчик (+25% к XP Пасса)"},
    "Рико": {"rarity": "🔵 Сверхредкий", "bonus": "Рикошет (30% шанс вернуть ставку)"},
    "Джесси": {"rarity": "🔵 Сверхредкий", "bonus": "Инженер (+5 кубков в Броулболе)"},
    "Динамайк": {"rarity": "🔵 Сверхредкий", "bonus": "Подрывник (+50 монет в ШД)"},
    "Эдгар": {"rarity": "💜 Эпический", "bonus": "Агро-хил (Высокий винрейт, -3 кубка)"},
    "Пайпер": {"rarity": "💜 Эпический", "bonus": "Снайпер (+2% к винрейту за уровень сил)"},
    "Мортис": {"rarity": "🟥 Мифический", "bonus": "Хардкор (+15 кубков за победу)"},
    "Леон": {"rarity": "🟨 Легендарный", "bonus": "Инвиз (Потери при сливе всего -2 кубка)"},
    "Спайк": {"rarity": "🟨 Легендарный", "bonus": "Кактус (+50% золото из Starr Drops)"},
    "Корделиус": {"rarity": "🟨 Легендарный", "bonus": "Царство грибов (+5 гемов с дропа)"},
    "Вольт": {"rarity": "🌟 Хроматический", "bonus": "Максимум силы (+5% золота за ур. силы)"}
}

COSMETIC_POOL = {
    "icons": ["💀 Череп Brawl", "👑 Vasanin Топ-1", "🔥 Огненный Феникс", "👾 Ретро-Геймер", "🌟 Звезда 2026", "player_icon_rico_brawlentines.jpg"],
    "pins": ["👍 Шелли Лайк", "😭 Грустный Эдгар", "🤖 Сту Агро-Пин", "😎 Кольт Крутой", "😡 Булл Злится", "emoji_bp_street_gg.png"],
    "sprays": ["🎨 Спрей ХАОС (+15 монет)", "⚡ Спрей МЛГ (+15 монет)", "👑 Спрей Корона (+15 монет)", "❌ Спрей КРЕСТ (+15 монет)"]
}

def get_player(user_id, username="Игрок"):
    if user_id not in players:
        players[user_id] = {
            'name': username,
            'coins': 2000,
            'gems': 600,
            'cups': 0,
            'pass_xp': 0,
            'clan': None,
            'wins': 0,
            'used_promos': [],
            'selected_brawler': "Шелли",
            'brawlers': {"Шелли": 1}, 
            'boxes': 0,
            'hypercharges': [],
            'mastery': {"Шелли": 0},
            'skins': [],
            'friends': [],  
            'cosmetics': {
                'unlocked_icons': ["💀 Череп Brawl"],
                'unlocked_pins': ["👍 Шелли Лайк"],
                'unlocked_sprays': ["❌ Спрей КРЕСТ (+15 монет)"],
                'active_icon': "💀 Череп Brawl",
                'active_pin': "👍 Шелли Лайк",
                'active_spray': "❌ Спрей КРЕСТ (+15 монет)"
            }
        }
    return players[user_id]

def get_main_markup(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⚔️ В бой!", "👤 Профиль")
    markup.add("🛍 Магазин", "✨ Starr Drops")
    markup.add("💪 Прокачка", "💎 Донат")
    markup.add("🛡️ Кланы", "🎰 Казино")
    markup.add("🎫 Пасс", "🏆 Топ игроков")
    markup.add("👥 Друзья", "🎨 Настроить Косметику")
    markup.add("🎫 Промокоды", "⚙️ Настройки")
    if user_id in ADMINS:
        markup.add("👑 Админ-Панель")
    markup.add("Назад")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or f"User_{user_id}"
    get_player(user_id, name)
    bot.send_message(message.chat.id, f"🔥 Бот запущен! Добавлена секретная текстовая команда на выдачу админки.", reply_markup=get_main_markup(user_id))

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_player(user_id)
    
    if call.data == "admin_give_resources" and user_id in ADMINS:
        user['coins'] += 50000
        user['gems'] += 5000
        bot.answer_callback_query(call.id, "💰 Успешно начислено 50,000 монет и 5,000 гемов!", show_alert=True)
        
    elif call.data == "admin_global_broadcast" and user_id in ADMINS:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📢 Введи текст для рассылки всем игрокам:")
        bot.register_next_step_handler(msg, process_broadcast_text)

    elif call.data == "admin_add_new_admin" and user_id in ADMINS:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "👤 Введи Telegram ID игрока, которому хочешь дать АДМИНКУ:")
        bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "friend_add_action":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🆔 Введи ID игрока, которого хочешь добавить в друзья:")
        bot.register_next_step_handler(msg, process_add_friend)

    elif call.data == "buy_ollie_jake":
        if "Олли Jake" in user.get('skins', []):
            bot.answer_callback_query(call.id, "❌ У тебя уже есть этот эксклюзивный пак!", show_alert=True)
            return
        if user['gems'] >= 555:
            user['gems'] -= 555
            user.setdefault('skins', []).append("Олли Jake")
            if "player_icon_rico_brawlentines.jpg" not in user['cosmetics']['unlocked_icons']:
                user['cosmetics']['unlocked_icons'].append("player_icon_rico_brawlentines.jpg")
            if "emoji_bp_street_gg.png" not in user['cosmetics']['unlocked_pins']:
                user['cosmetics']['unlocked_pins'].append("emoji_bp_street_gg.png")
            bot.answer_callback_query(call.id, "🎉 Пачка Олли Jake успешно куплена!", show_alert=True)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно гемов! Нужно 555 💎", show_alert=True)

    elif call.data.startswith("set_icon_"):
        icon = call.data.replace("set_icon_", "")
        user['cosmetics']['active_icon'] = icon
        bot.answer_callback_query(call.id, f"Иконка изменена!")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        
    elif call.data.startswith("set_pin_"):
        pin = call.data.replace("set_pin_", "")
        user['cosmetics']['active_pin'] = pin
        bot.answer_callback_query(call.id, f"Пин экипирован!")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data.startswith("view_brawler_"):
        brawler = call.data.replace("view_brawler_", "")
        lvl = user['brawlers'].get(brawler, 1)
        mastery = user.get('mastery', {}).get(brawler, 0)
        has_hc = "🔥 АКТИВИРОВАН" if brawler in user.get('hypercharges', []) else "❌ НЕ КУПЛЕН"
        b_info = ALL_BRAWLERS.get(brawler, {"rarity": "🟢 Редкий", "bonus": "Нет"})
        
        text = f"ℹ️ **БРАВЛЕР: {brawler}**\n━━━━━━━━━━━━━━━━━━━\n⭐ Редкость: {b_info['rarity']}\n🧪 Сила: **{lvl}/11**\n🔮 Мастерство: **{mastery} XP**\n⚡ Гиперзаряд: **{has_hc}**\n📋 Пассивка: *{b_info['bonus']}*\n"
        inline_confirm = telebot.types.InlineKeyboardMarkup()
        inline_confirm.add(telebot.types.InlineKeyboardButton(text=f"🎯 Взять {brawler} в бой", callback_data=f"equip_brawler_{brawler}"))
        inline_confirm.add(telebot.types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_selection"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=inline_confirm, parse_mode="Markdown")

    elif call.data.startswith("equip_brawler_"):
        brawler = call.data.replace("equip_brawler_", "")
        user['selected_brawler'] = brawler
        markup_battle = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup_battle.add("🌵 Одиночное Столкновение", "⚽ Броулбол", "Назад")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, f"✅ **{brawler} выбран!**", reply_markup=markup_battle)

    elif call.data == "back_to_selection":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        inline_choose = telebot.types.InlineKeyboardMarkup(row_width=2)
        buttons = [telebot.types.InlineKeyboardButton(text=f"{'🎯 ' if user['selected_brawler'] == b else ''}{b}", callback_data=f"view_brawler_{b}") for b in user['brawlers'].keys()]
        inline_choose.add(*buttons)
        bot.send_message(call.message.chat.id, "🦸‍♂️ **ВЫБОР БОЙЦА**:", reply_markup=inline_choose)

    elif call.data == "roll_starr_drop":
        roll = random.random()
        coins_add = 150
        cosmetic_drop = None
        drop_type = ""
        if roll < 0.25:
            drop_type = random.choice(["icons", "pins"])
            cosmetic_drop = random.choice(COSMETIC_POOL[drop_type])
            if cosmetic_drop in ["player_icon_rico_brawlentines.jpg", "emoji_bp_street_gg.png"]:
                cosmetic_drop = COSMETIC_POOL[drop_type][0]
            if drop_type == "icons" and cosmetic_drop not in user['cosmetics']['unlocked_icons']:
                user['cosmetics']['unlocked_icons'].append(cosmetic_drop)
            elif drop_type == "pins" and cosmetic_drop not in user['cosmetics']['unlocked_pins']:
                user['cosmetics']['unlocked_pins'].append(cosmetic_drop)

        user['coins'] += coins_add
        report = f"✨ **СТАРР ДРОП ОТКРЫТ!** ✨\n━━━━━━━━━━━━━━━\n💰 Монеты: +{coins_add}"
        if cosmetic_drop:
            report += f"\n\n🎨 **КОСМЕТИКА!**\nВыбито: **{cosmetic_drop}**"
        bot.send_message(call.message.chat.id, report)
        bot.answer_callback_query(call.id)

def process_add_admin(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_markup(message.from_user.id))
        return
    try:
        new_admin_id = int(message.text)
        if new_admin_id in ADMINS:
            bot.send_message(message.chat.id, "❌ Этот игрок уже является админом!", reply_markup=get_main_markup(message.from_user.id))
        else:
            ADMINS.append(new_admin_id)
            bot.send_message(message.chat.id, f"✅ ID `{new_admin_id}` назначен АДМИНИСТРАТОРОМ!", parse_mode="Markdown", reply_markup=get_main_markup(message.from_user.id))
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ID.", reply_markup=get_main_markup(message.from_user.id))

def process_add_friend(message):
    user_id = message.from_user.id
    user = get_player(user_id)
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_markup(user_id))
        return
    try:
        friend_id = int(message.text)
        if friend_id == user_id:
            bot.send_message(message.chat.id, "❌ Нельзя добавить самого себя!", reply_markup=get_main_markup(user_id))
            return
        if friend_id in user.get('friends', []):
            bot.send_message(message.chat.id, "❌ Уже в друзьях!", reply_markup=get_main_markup(user_id))
            return
        if friend_id in players:
            user.setdefault('friends', []).append(friend_id)
            friend_user = get_player(friend_id)
            friend_user.setdefault('friends', []).append(user_id)
            bot.send_message(message.chat.id, f"🤝 Вы подружились с игроком **{friend_user['name']}**!", parse_mode="Markdown", reply_markup=get_main_markup(user_id))
        else:
            bot.send_message(message.chat.id, "❌ Игрок не найден в боте!", reply_markup=get_main_markup(user_id))
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка в ID.", reply_markup=get_main_markup(user_id))

def process_broadcast_text(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_markup(message.from_user.id))
        return
    count = 0
    for u_id in players.keys():
        try:
            bot.send_message(u_id, f"📢 **ОБЪЯВЛЕНИЕ ОТ АДМИНИСТРАЦИИ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Успешно отправлено {count} игрокам.", reply_markup=get_main_markup(message.from_user.id))

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    user = get_player(user_id, name)

    # 👑 СЕКРЕТНАЯ КОМАНДА ДЛЯ ВЛАДЕЛЬЦА БОТА
    # Пример использования: /giveadmin 987654321
    if message.text.startswith("/giveadmin"):
        if user_id != CREATOR_ID:
            bot.send_message(message.chat.id, "❌ У тебя нет прав разработчика для использования этой команды!")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Ошибка! Пиши команду вот так: `/giveadmin ТГ_ИД`", parse_mode="Markdown")
            return
            
        try:
            target_id = int(parts[1])
            if target_id in ADMINS:
                bot.send_message(message.chat.id, f"❌ Этот игрок (ID: `{target_id}`) уже админ!", parse_mode="Markdown")
            else:
                ADMINS.append(target_id)
                bot.send_message(message.chat.id, f"👑 Успешно! Игроку `{target_id}` выданы права администратора через секретную команду!", parse_mode="Markdown")
                try:
                    bot.send_message(target_id, "👑 **Создатель выдал тебе админку!** Перезапусти бота кнопкой /start, чтобы активировать панель.")
                except: pass
        except ValueError:
            bot.send_message(message.chat.id, "❌ Ошибка! ID должен состоять только из цифр.")
        return

    if message.text.lower() == "only2026":
        if "only2026" in user.get('used_promos', []):
            bot.send_message(message.chat.id, "❌ Промокод уже использован!", reply_markup=get_main_markup(user_id))
        else:
            user['coins'] += 1; user['gems'] += 1; user['boxes'] = user.get('boxes', 0) + 1
            user.setdefault('used_promos', []).append("only2026")
            bot.send_message(message.chat.id, "🎉 **only2026 активирован!**", reply_markup=get_main_markup(user_id))
        return

    if message.text == "👑 Админ-Панель" and user_id in ADMINS:
        inline_admin = telebot.types.InlineKeyboardMarkup(row_width=1)
        inline_admin.add(
            telebot.types.InlineKeyboardButton("💰 Начислить ресурсы (+50к голды, +5к гемов)", callback_data="admin_give_resources"),
            telebot.types.InlineKeyboardButton("📢 Сделать глобальную рассылку", callback_data="admin_global_broadcast"),
            telebot.types.InlineKeyboardButton("➕ Добавить админа по ID", callback_data="admin_add_new_admin")
        )
        bot.send_message(message.chat.id, f"👑 **ПАНЕЛЬ РАЗРАБОТЧИКА**", reply_markup=inline_admin)

    elif message.text == "👥 Друзья":
        inline_friends = telebot.types.InlineKeyboardMarkup()
        inline_friends.add(telebot.types.InlineKeyboardButton("➕ Добавить друга по ID", callback_data="friend_add_action"))
        f_list = []
        for f_id in user.get('friends', []):
            if f_id in players:
                f_user = players[f_id]
                f_list.append(f"• 👤 {f_user['name']} | 🏆 {f_user['cups']} кубков (ID: `{f_id}`)")
        f_list_str = "У тебя пока нет друзей." if not f_list else "\n".join(f_list)
        friends_text = f"👥 **ТВОИ ДРУЗЬЯ**\n━━━━━━━━━━━━━━━━━━━━━\n🆔 Твой ID: `{user_id}`\n\n📋 Список:\n{f_list_str}"
        bot.send_message(message.chat.id, friends_text, reply_markup=inline_friends, parse_mode="Markdown")

    elif message.text == "🛍 Магазин":
        inline_shop = telebot.types.InlineKeyboardMarkup()
        inline_shop.add(telebot.types.InlineKeyboardButton("🟢 Купить Пак 'Олли Jake' (555 💎)", callback_data="buy_ollie_jake"))
        shop_text = "🛍 **МАГАЗИН ВАСАНИН БРАВЛ**\n━━━━━━━━━━━━━━━━━━━━━\n⚡ **Гипер-Пак: Олли Jake**\n• Скин: *Олли Jake*\n• Иконка: `player_icon_rico_brawlentines.jpg`\n• Значок: `emoji_bp_street_gg.png`\n\n💰 Стоимость: **555 гемов**"
        bot.send_message(message.chat.id, shop_text, reply_markup=inline_shop, parse_mode="Markdown")

    elif message.text == "⚔️ В бой!":
        inline_choose = telebot.types.InlineKeyboardMarkup(row_width=2)
        buttons = [telebot.types.InlineKeyboardButton(text=f"{'🎯 ' if user['selected_brawler'] == b else ''}{b}", callback_data=f"view_brawler_{b}") for b in user['brawlers'].keys()]
        inline_choose.add(*buttons)
        bot.send_message(message.chat.id, "🦸‍♂️ **МЕНЮ ВЫБОР БОЙЦА**:", reply_markup=inline_choose)

    elif message.text in ["🌵 Одиночное Столкновение", "⚽ Броулбол"]:
        cb = user['selected_brawler']
        lvl = user['brawlers'].get(cb, 1)
        if random.random() < (0.50 + (lvl - 1) * 0.04):
            user['cups'] += 10; user['coins'] += 30
            res = f"🔥 **ПОБЕДА!** Награды: +10 🏆, +30 💰"
        else:
            user['cups'] = max(0, user['cups'] - 7)
            res = f"❌ **ПОРАЖЕНИЕ!** Потеряно: -7 🏆."
        bot.send_message(message.chat.id, res, reply_markup=get_main_markup(user_id))

    elif message.text == "🎨 Настроить Косметику":
        inline_choose = telebot.types.InlineKeyboardMarkup(row_width=1)
        for ic in user['cosmetics']['unlocked_icons']:
            inline_choose.add(telebot.types.InlineKeyboardButton(f"🖼️ Поставить {ic}", callback_data=f"set_icon_{ic}"))
        for p in user['cosmetics']['unlocked_pins']:
            inline_choose.add(telebot.types.InlineKeyboardButton(f"💬 Экипировать {p}", callback_data=f"set_pin_{p}"))
        bot.send_message(message.chat.id, "🎨 **ГАРДЕРОБ КОСМЕТИКИ**:", reply_markup=inline_choose)

    elif message.text == "👤 Профиль":
        c_icon = user['cosmetics']['active_icon']
        b_list = [f"• {b} [Сила {l}]" for b, l in user['brawlers'].items()]
        s_list = [f"• {s}" for s in user.get('skins', [])]
        if not s_list: s_list = ["• Нет скинов"]
        
        card = f"👑 **АККАУНТ: {user['name']}**\n🆔 ID: `{user_id}`\n━━━━━━━━━━━━━━━━━━━━━\n💬 Пин: `{user['cosmetics']['active_pin']}`\n🎯 В бою: **{user['selected_brawler']}**\n🏆 Кубки: {user['cups']} | 💰 Монеты: {user['coins']} | 💎 Гемы: {user['gems']}\n\n👕 Скины:\n" + "\n".join(s_list) + "\n\n🦸‍♂️ Бравлеры:\n" + "\n".join(b_list)

        if c_icon.endswith(".jpg") or c_icon.endswith(".png"):
            if os.path.exists(c_icon):
                with open(c_icon, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=f"🖼️ **Иконка активна!**\n\n" + card, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"🖼️ (Ошибка файла: `{c_icon}`)\n\n" + card, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"🖼️ Иконка: `{c_icon}`\n\n" + card, parse_mode="Markdown")

    elif message.text == "✨ Starr Drops":
        inline_starr = telebot.types.InlineKeyboardMarkup()
        inline_starr.add(telebot.types.InlineKeyboardButton("🟡 Открыть Starr Drop 🟡", callback_data="roll_starr_drop"))
        bot.send_message(message.chat.id, "✨ Симулятор Старр Дропсов!", reply_markup=inline_starr)

    elif message.text == "🎫 Промокоды":
        bot.send_message(message.chat.id, "🎫 Просто напиши рабочий промокод в чат для активации!")

    elif message.text == "💪 Прокачка":
        bot.send_message(message.chat.id, "💪 Меню прокачки бравлеров временно на техобслуживании, скоро заработает!")

    elif message.text == "💎 Донат":
        bot.send_message(message.chat.id, "💎 Донат-магазин закрыт. Используй админку, чтобы начислять себе любые ресурсы!")

    elif message.text == "🛡️ Кланы":
        bot.send_message(message.chat.id, "🛡️ Система кланов готовится к глобальному обновлению!")

    elif message.text == "🎰 Казино":
        bot.send_message(message.chat.id, "🎰 Казино временно закрыто шерифом Шелли на чистку игровых автоматов.")

    elif message.text == "🎫 Пасс":
        bot.send_message(message.chat.id, "🎫 Текущий сезон Brawl Pass завершен. Ожидай новый сезон!")

    elif message.text == "🏆 Топ игроков":
        bot.send_message(message.chat.id, "🏆 Таблица лидеров обновляется каждую неделю. Ты на правильном пути!")

    elif message.text == "⚙️ Настройки":
        bot.send_message(message.chat.id, "⚙️ Настройки аккаунта: Язык: RU. Сервер: Replit Cloud 2026.")

    elif message.text == "Назад":
        bot.send_message(message.chat.id, "В меню.", reply_markup=get_main_markup(user_id))

@app.route('/')
def home(): return "Server OK"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
