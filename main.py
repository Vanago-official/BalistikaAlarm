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
import database

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

app = Client(
    "my_account",
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

def get_keyboard():
    kb = [
        [KeyboardButton(text="Підписатись"), KeyboardButton(text="Відписатись")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer("Головне меню. Оберіть дію на клавіатурі:", reply_markup=get_keyboard())

@dp.message(F.text == "Підписатись")
async def subscribe_action(message: types.Message):
    database.add_user(message.from_user.id)
    await message.answer("Ви успішно підписалися на сповіщення!", reply_markup=get_keyboard())

@dp.message(F.text == "Відписатись")
async def unsubscribe_action(message: types.Message):
    database.remove_user(message.from_user.id)
    await message.answer("Ви відписалися від сповіщень.", reply_markup=get_keyboard())

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
        
        alert_text = f"{timestamp}\nWARNING: {words_str}\n\n@{chat_name} - {full_text}"
        
        print(f"\n{'-'*30}\n{alert_text}\n{'-'*30}\n")
        
        subscribed_users = database.load_users()
        for user_id in subscribed_users:
            try:
                await bot.send_message(chat_id=user_id, text=alert_text)
            except Exception as e:
                logging.error(e)

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
