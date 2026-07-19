import asyncio

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import logging
import string
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from pyrogram import Client, filters
from pyrogram.types import Message

import config
from database import UserManager

logging.basicConfig(level=logging.INFO)

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
        [KeyboardButton(text="Розм'ютити")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer("Головне меню. Оберіть дію на клавіатурі:", reply_markup=get_keyboard())

@dp.message(F.text == "Підписатись")
async def subscribe_action(message: types.Message):
    user_manager.add_user(message.from_user.id)
    await message.answer("Ви успішно підписалися на сповіщення!", reply_markup=get_keyboard())

@dp.message(F.text == "Відписатись")
async def unsubscribe_action(message: types.Message):
    user_manager.remove_user(message.from_user.id)
    await message.answer("Ви відписалися від сповіщень.", reply_markup=get_keyboard())

@dp.message(F.text == "Розм'ютити")
async def unmute_action(message: types.Message):
    success = user_manager.unmute_user(message.from_user.id)
    if success:
        await message.answer("Сповіщення відновлено! Ви почуєте про наступну загрозу.", reply_markup=get_keyboard())
    else:
        await message.answer("Ви ще не підписані. Натисніть 'Підписатись'.", reply_markup=get_keyboard())

@app.on_message(filters.chat(config.CHANNELS_TO_MONITOR))
async def handle_channel_message(client: Client, message: Message):
    text = message.text or message.caption
    if not text:
        return
    
    clean_text = text.lower()
    clean_text = clean_text.translate(str.maketrans('', '', string.punctuation))
    
    found_words = [word for word in config.TARGET_WORDS if word.lower() in clean_text]
    
    if found_words:
        chat_title = message.chat.title
        chat_name = f"@{message.chat.username}" if message.chat.username else chat_title
        
        timestamp = datetime.now().strftime("%d:%m:%Y %H:%M")
        words_str = ", ".join(found_words)
        full_text = message.text or message.caption or ""
        
        alert_text = f"{timestamp}\nWARNING: {words_str}\n\n{chat_name} - {full_text}"
        
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
