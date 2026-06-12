import telebot
import os
import random
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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

MODIFIERS = [
    "🤖 Робот-Босс (+50 монет награды, повышенный риск слить!)", 
    "🥤 Энергетический напиток (+15% к шансу победы!)", 
    "☄️ Метеоритный дождь (Классический жесткий замес)"
]

def get_player(user_id, username="Игрок"):
    if user_id not in players:
        players[user_id] = {
            'name': username,
            'coins': 2000,
            'gems': 600,  # Даем чуть больше гемов на старте для теста пака
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
            'skins': [],  # Список купленных скинов
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

user_states = {}

def get_main_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("⚔️ В бой!", "👤 Профиль")
    markup.add("🛍 Магазин", "✨ Starr Drops")
    markup.add("🎫 Промокоды", "🎨 Настроить Косметику")
    markup.add("Назад")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or f"User_{user_id}"
    get_player(user_id, name)
    bot.send_message(message.chat.id, f"🔥 Добро пожаловать! Эксклюзивный пак «Олли Jake» уже доступен в Магазине!", reply_markup=get_main_markup())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_player(user_id)
    
    # Покупка пака Олли Jake
    if call.data == "buy_ollie_jake":
        if "Олли Jake" in user.get('skins', []):
            bot.answer_callback_query(call.id, "❌ У тебя уже есть этот эксклюзивный пак!", show_alert=True)
            return
        
        if user['gems'] >= 555:
            user['gems'] -= 555
            user.setdefault('skins', []).append("Олли Jake")
            
            # Добавляем иконку и пин в инвентарь
            if "player_icon_rico_brawlentines.jpg" not in user['cosmetics']['unlocked_icons']:
                user['cosmetics']['unlocked_icons'].append("player_icon_rico_brawlentines.jpg")
            if "emoji_bp_street_gg.png" not in user['cosmetics']['unlocked_pins']:
                user['cosmetics']['unlocked_pins'].append("emoji_bp_street_gg.png")
                
            bot.answer_callback_query(call.id, "🎉 Успешно! Пак Олли Jake добавлен на аккаунт!", show_alert=True)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно гемов! Нужно 555 💎", show_alert=True)

    # Экипировка косметики
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
        
    elif call.data.startswith("set_spray_"):
        spray = call.data.replace("set_spray_", "")
        user['cosmetics']['active_spray'] = spray
        bot.answer_callback_query(call.id, f"Спрей выбран!")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    # Логика выбора бойцов
    elif call.data.startswith("view_brawler_"):
        brawler = call.data.replace("view_brawler_", "")
        lvl = user['brawlers'].get(brawler, 1)
        mastery = user.get('mastery', {}).get(brawler, 0)
        has_hc = "🔥 АКТИВИРОВАН" if brawler in user.get('hypercharges', []) else "❌ НЕ КУПЛЕН"
        b_info = ALL_BRAWLERS.get(brawler, {"rarity": "🟢 Редкий", "bonus": "Нет"})
        
        text = f"ℹ️ **БРАВЛЕР: {brawler}**\n━━━━━━━━━━━━━━━━━━━\n⭐ Редкость: {b_info['rarity']}\n🧪 Сила: **{lvl}/11**\n🔮 Мастерство: **{mastery} XP**\n⚡  Гиперзаряд: **{has_hc}**\n📋 Пассивка: *{b_info['bonus']}*\n"
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

    # Открытие Starr Drops
    elif call.data == "roll_starr_drop":
        roll = random.random()
        coins_add = 150
        cosmetic_drop = None
        drop_type = ""

        if roll < 0.25:
            drop_type = random.choice(["icons", "pins", "sprays"])
            cosmetic_drop = random.choice(COSMETIC_POOL[drop_type])
            
            # Исключаем из обычного дропа эксклюзивы из платного пака
            if cosmetic_drop in ["player_icon_rico_brawlentines.jpg", "emoji_bp_street_gg.png"]:
                cosmetic_drop = COSMETIC_POOL[drop_type][0]

            if drop_type == "icons" and cosmetic_drop not in user['cosmetics']['unlocked_icons']:
                user['cosmetics']['unlocked_icons'].append(cosmetic_drop)
            elif drop_type == "pins" and cosmetic_drop not in user['cosmetics']['unlocked_pins']:
                user['cosmetics']['unlocked_pins'].append(cosmetic_drop)
            elif drop_type == "sprays" and cosmetic_drop not in user['cosmetics']['unlocked_sprays']:
                user['cosmetics']['unlocked_sprays'].append(cosmetic_drop)

        user['coins'] += coins_add
        report = f"✨ **СТАРР ДРОП ОТКРЫТ!** ✨\n━━━━━━━━━━━━━━━\n💰 Монеты: +{coins_add}"
        if cosmetic_drop:
            report += f"\n\n🎨 **КОСМЕТИКА!**\nВыбито: **{cosmetic_drop}**"
        
        bot.send_message(call.message.chat.id, report)
        bot.answer_callback_query(call.id)

# --- ОБРАБОТКА ТЕКСТА ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    user = get_player(user_id, name)

    if message.text == "🛍 Магазин":
        inline_shop = telebot.types.InlineKeyboardMarkup()
        inline_shop.add(telebot.types.InlineKeyboardButton("🟢 Купить Пак 'Олли Jake' (555 💎)", callback_data="buy_ollie_jake"))
        
        shop_text = (
            "🛍 **МАГАЗИН ВАСАНИН БРАВЛ**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 **АКТУАЛЬНОЕ ПРЕДЛОЖЕНИЕ:**\n"
            "⚡ **Гипер-Пак: Олли Jake**\n"
            "Содержимое пака:\n"
            "• 👕 Эксклюзивный скин: *Олли Jake*\n"
            "• 🖼️ Иконка профиля: `player_icon_rico_brawlentines.jpg`\n"
            "• 💬 Особый значок: `emoji_bp_street_gg.png`\n\n"
            "💰 Стоимость: **555 гемов**"
        )
        bot.send_message(message.chat.id, shop_text, reply_markup=inline_shop, parse_mode="Markdown")

    elif message.text == "⚔️ В бой!":
        inline_choose = telebot.types.InlineKeyboardMarkup(row_width=2)
        buttons = [telebot.types.InlineKeyboardButton(text=f"{'🎯 ' if user['selected_brawler'] == b else ''}{b}", callback_data=f"view_brawler_{b}") for b in user['brawlers'].keys()]
        inline_choose.add(*buttons)
        bot.send_message(message.chat.id, "🦸‍♂️ **МЕНЮ ВЫБОР БОЙЦА**:", reply_markup=inline_choose)

    elif message.text in ["🌵 Одиночное Столкновение", "⚽ Броулбол"]:
        cb = user['selected_brawler']
        lvl = user['brawlers'].get(cb, 1)
        
        win_chance = 0.50 + (lvl - 1) * 0.04
        has_hc = cb in user.get('hypercharges', [])
        if has_hc: win_chance += 0.25

        if random.random() < win_chance:
            cups_win = 20 if has_hc else 10
            gold_win = 60 if has_hc else 30
            
            if user['cosmetics']['active_spray']:
                gold_win += 15
                spray_bonus = " (+15 монет от Спрея!)"
            else: spray_bonus = ""

            user['cups'] += cups_win; user['coins'] += gold_win; user['wins'] += 1
            user.setdefault('mastery', {})[cb] = user['mastery'].get(cb, 0) + 15
            
            res = f"🔥 **ПОБЕДА!**\nБоец: {cb}\nНаграды: +{cups_win} 🏆, +{gold_win} 💰{spray_bonus}"
        else:
            cups_lose = 2 if cb == "Леон" else 7
            user['cups'] = max(0, user['cups'] - cups_lose)
            res = f"❌ **ПОРАЖЕНИЕ!** Потеряно: -{cups_lose} 🏆."

        bot.send_message(message.chat.id, res, reply_markup=get_main_markup())

    elif message.text == "🎨 Настроить Косметику":
        inline_choose = telebot.types.InlineKeyboardMarkup(row_width=1)
        for ic in user['cosmetics']['unlocked_icons']:
            inline_choose.add(telebot.types.InlineKeyboardButton(f"🖼️ Поставить {ic}", callback_data=f"set_icon_{ic}"))
        for p in user['cosmetics']['unlocked_pins']:
            inline_choose.add(telebot.types.InlineKeyboardButton(f"💬 Экипировать {p}", callback_data=f"set_pin_{p}"))
        for sp in user['cosmetics']['unlocked_sprays']:
            inline_choose.add(telebot.types.InlineKeyboardButton(f"🖌️ Напылить {sp}", callback_data=f"set_spray_{sp}"))

        bot.send_message(message.chat.id, "🎨 **ГАРДЕРОБ КОСМЕТИКИ**:", reply_markup=inline_choose)

    elif message.text == "👤 Профиль":
        c_icon = user['cosmetics']['active_icon']
        c_pin = user['cosmetics']['active_pin']
        c_spray = user['cosmetics']['active_spray']
        
        b_list = [f"• {b} [Сила {l}]" for b, l in user['brawlers'].items()]
        s_list = [f"• {s}" for s in user.get('skins', [])]
        if not s_list: s_list = ["• Нет скинов"]
        
        card = (
            f"🖼️ Иконка профиля: `{c_icon}`\n"
            f"👑 **АККАУНТ: {user['name']}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 Экипированный Пин: `{c_pin}`\n"
            f"🖌️ Спрей: {c_spray}\n"
            f"🎯 В бою: **{user['selected_brawler']}**\n"
            f"🏆 Кубки: {user['cups']} | 💰 Монеты: {user['coins']} | 💎 Гемы: {user['gems']}\n\n"
            f"👕 Купленные скины:\n" + "\n".join(s_list) + "\n\n"
            f"🦸‍♂️ Твои бравлеры:\n" + "\n".join(b_list)
        )
        bot.send_message(message.chat.id, card)

    elif message.text == "✨ Starr Drops":
        inline_starr = telebot.types.InlineKeyboardMarkup()
        inline_starr.add(telebot.types.InlineKeyboardButton("🟡 Открыть Starr Drop 🟡", callback_data="roll_starr_drop"))
        bot.send_message(message.chat.id, "✨ Симулятор Старр Дропсов!", reply_markup=inline_starr)

    elif message.text == "Назад":
        bot.send_message(message.chat.id, "В меню.", reply_markup=get_main_markup())

@app.route('/')
def home(): return "Server OK"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True)).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
