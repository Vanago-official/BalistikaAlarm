import asyncio

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import logging
import string
import re
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from pyrogram import Client, filters
from pyrogram.types import Message

import config
from database import UserManager

logging.basicConfig(level=logging.INFO)

EXACT_THREATS_RX = [re.compile(p, re.IGNORECASE) for p in getattr(config, 'EXACT_THREATS', [])]
WEAPONS_RX = [re.compile(p, re.IGNORECASE) for p in getattr(config, 'WEAPONS', [])]
ACTION_WORDS_RX = [re.compile(p, re.IGNORECASE) for p in getattr(config, 'ACTION_WORDS', [])]
CANCEL_WORDS_RX = [re.compile(p, re.IGNORECASE) for p in getattr(config, 'CANCEL_WORDS', [])]
NEWS_WORDS_RX = [re.compile(p, re.IGNORECASE) for p in getattr(config, 'NEWS_WORDS', [])]
CLEAR_WORDS_RX = [re.compile(p, re.IGNORECASE) for p in getattr(config, 'CLEAR_WORDS', [])]

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

app = Client(
    "my_account",
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

user_manager = UserManager()

def get_keyboard():
    kb = [
        [KeyboardButton(text="Підписатись"), KeyboardButton(text="Відписатись")],
        [KeyboardButton(text="Розм'ютити"), KeyboardButton(text="Зам'ютити")],
        [KeyboardButton(text="Статус"), KeyboardButton(text="Інфо")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer("Головне меню. Оберіть дію на клавіатурі:", reply_markup=get_keyboard())

@dp.message(F.text == "Підписатись")
async def subscribe_action(message: types.Message):
    user_manager.add_user(message.from_user.id)
    logging.info(f"Користувач {message.from_user.id} ПІДПИСАВСЯ.")
    await message.answer("Ви успішно підписалися на сповіщення!", reply_markup=get_keyboard())

@dp.message(F.text == "Відписатись")
async def unsubscribe_action(message: types.Message):
    user_manager.remove_user(message.from_user.id)
    logging.info(f"Користувач {message.from_user.id} ВІДПИСАВСЯ.")
    await message.answer("Ви відписалися від сповіщень.", reply_markup=get_keyboard())

@dp.message(F.text == "Розм'ютити")
async def unmute_action(message: types.Message):
    success = user_manager.unmute_user(message.from_user.id)
    if success:
        logging.info(f"Користувач {message.from_user.id} РОЗМ'ЮТИВСЯ.")
        await message.answer("Сповіщення відновлено! Ви почуєте про наступну загрозу.", reply_markup=get_keyboard())
    else:
        await message.answer("Ви ще не підписані. Натисніть 'Підписатись'.", reply_markup=get_keyboard())

@dp.message(F.text == "Зам'ютити")
async def mute_action(message: types.Message):
    success = user_manager.mute_user(message.from_user.id)
    if success:
        logging.info(f"Користувач {message.from_user.id} ЗАМ'ЮТИВСЯ.")
        await message.answer("Сповіщення тимчасово вимкнено. Ви не будете отримувати тривоги, поки не натиснете 'Розм'ютити' або поки не буде відбою.", reply_markup=get_keyboard())
    else:
        await message.answer("Ви ще не підписані. Натисніть 'Підписатись'.", reply_markup=get_keyboard())

@dp.message(F.text == "Статус")
async def status_action(message: types.Message):
    user = user_manager.get_user(message.from_user.id)
    if not user:
        await message.answer("Ви не підписані на сповіщення. Натисніть 'Підписатись'.", reply_markup=get_keyboard())
    elif user.muted:
        await message.answer("Ваш статус: ЗАМ'ЮЧЕНО\nВи не будете отримувати тривоги до наступного відбою або поки не натиснете 'Розм'ютити'.", reply_markup=get_keyboard())
    else:
        await message.answer("Ваш статус: АКТИВНО\nВи отримуєте всі сповіщення про нові загрози.", reply_markup=get_keyboard())

@dp.message(F.text == "Інфо")
async def info_action(message: types.Message):
    info_text = (
        "ℹ️ <b>Інформація про бота</b>\n\n"
        "Цей бот моніторить канали на наявність повідомлень про швидкісні цілі та балістику.\n\n"
        "• <b>Підписатись</b> — отримувати сповіщення\n"
        "• <b>Відписатись</b> — повністю перестати отримувати сповіщення\n"
        "• <b>Зам'ютити</b> — тимчасово вимкнути сповіщення (наприклад, якщо ви вже в укритті)\n"
        "• <b>Розм'ютити</b> — увімкнути сповіщення знову\n"
        "• <b>Статус</b> — перевірити, чи увімкнені у вас зараз сповіщення\n\n"
        "<i>При надсиланні тривоги бот м'ютить вас автоматично, щоб не спамити. При відбої — розм'ючує.</i>"
    )
    await message.answer(info_text, parse_mode="HTML", reply_markup=get_keyboard())

@app.on_message(filters.chat(config.CHANNELS_TO_MONITOR))
@app.on_edited_message(filters.chat(config.CHANNELS_TO_MONITOR))
async def handle_channel_message(client: Client, message: Message):
    text = message.text or message.caption
    if not text:
        return
    
    chat_title = message.chat.title or "Unknown Chat"
    # Щоб не спамити повними текстами, виводимо перші 100 символів
    logging.info(f"[Повідомлення з {chat_title}] {text[:100]}...")
    
    clean_text = text.lower()
    # Замінюємо пунктуацію на пробіли (крім апострофів), щоб уникнути злипання слів
    clean_text = re.sub(r"[^\w\s']", ' ', clean_text)
    
    # 1. Відбій
    clear_matched = [rx.search(clean_text) for rx in CLEAR_WORDS_RX if rx.search(clean_text)]
    if clear_matched:
        unmuted_ids = user_manager.unmute_all_users()
        for uid in unmuted_ids:
            try:
                await bot.send_message(chat_id=uid, text="Чисто. Ви знову отримуватимете сповіщення про нові загрози.", reply_markup=get_keyboard())
            except Exception as e:
                logging.error(e)
        return  # Зупиняємось, відбій оброблено
        
    # 2. Слова, що повністю скасовують тривогу (звіти, збиття)
    cancel_matched = [rx.search(clean_text) for rx in CANCEL_WORDS_RX if rx.search(clean_text)]
    if cancel_matched:
        return

    found_words = []
    
    # 3. Точні фрази (наприклад: "загроза балістики", "швидкісна ціль")
    # Точні фрази не блокуються новинами, оскільки це 100% загроза
    for rx in EXACT_THREATS_RX:
        match = rx.search(clean_text)
        if match:
            found_words.append(match.group(0).strip())
            
    # 4. Якщо точних фраз немає, перевіряємо слабшу комбінацію: "дія" + "зброя"
    if not found_words:
        # Спочатку перевіряємо, чи це не новини / зведення
        news_matched = [rx.search(clean_text) for rx in NEWS_WORDS_RX if rx.search(clean_text)]
        if not news_matched:
            weapons = [rx.search(clean_text).group(0).strip() for rx in WEAPONS_RX if rx.search(clean_text)]
            actions = [rx.search(clean_text).group(0).strip() for rx in ACTION_WORDS_RX if rx.search(clean_text)]
            
            if weapons and actions:
                found_words = weapons + actions

    if found_words:
        chat_title = message.chat.title
        chat_name = f"@{message.chat.username}" if message.chat.username else chat_title
        
        words_str = ", ".join(found_words)
        full_text = message.text or message.caption or ""
        
        alert_text = f"{timestamp}\nWARNING: {words_str}\n\n{chat_name} - {full_text}\n\nВас автоматично зам'ючено від спаму. Натисніть «Розм'ютити» на клавіатурі або дочекайтеся відбою."
        
        print(f"\n{'-'*30}\n{alert_text}\n{'-'*30}\n")
        
        users = user_manager.get_all_users()
        sent_any = False
        
        for user in users:
            # Метод send_alert сам перевіряє, чи не зам'ючений користувач, і м'ютить після відправки
            was_sent = await user.send_alert(bot, alert_text)
            if was_sent:
                sent_any = True
                
        # Зберігаємо базу, якщо хоча б одного користувача було щойно зам'ючено
        if sent_any:
            user_manager.save()

async def main():
    await app.start()
    try:
        await dp.start_polling(bot)
    finally:
        await app.stop()
    
if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
