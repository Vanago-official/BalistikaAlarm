import os
import asyncio

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
import configparser
from alert import get_alert
from database import *
from ai_handler import analyze_message

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

config = configparser.ConfigParser()
config.read("config.cfg")

CHANNELS = [x.strip() for x in config["Settings"]["CHANNELS"].split(",")]
CITY = config["Settings"]["CITY"]

app = Client(
    "balistika_alarm_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
)

userbot = Client(
    "@balistika_alarm_session",
    api_id=API_ID,
    api_hash=API_HASH,
)

alert_status = False


@app.on_message(filters.command("start"))
async def start_command(client, message):
    await add_user(message.chat.id)

    menu = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Activate")],
            [KeyboardButton("Deactivate")],
            [KeyboardButton("Mute")],
            [KeyboardButton("Unmute")],
            [KeyboardButton("Status")],
            [KeyboardButton("Info")],
        ],
        resize_keyboard=True
    )

    await message.reply_text(
        "Привіт! Я бот, який дозволяє моніторити прямі загрози балістики/ракет для м. Київ.",
        reply_markup=menu
    )

# FETCHING MESSAGES
@userbot.on_message(filters.chat(CHANNELS))
async def monitor_channels(client, message):
    global alert_status
    print(f"[MESSAGE] {source} - {text}")
    if not alert_status:
        return

    text = message.text or message.caption
    if not text:
        return

    ai_response = await analyze_message(text)

    if message.chat.username:
        source = f"@{message.chat.username}"
    else:
        source = message.chat.title

    print(f"[MESSAGE] {source} - {text}\n[AI] {ai_response}")

    if ai_response == "THREAT":
        users = await get_active_users()
        await set_all_mutes(1)
        for user_id in users:
            try:

                await app.send_message(
                    chat_id=user_id,
                    text=f"{source}\n{text}\n\n__You are muted until the all-clear signal.__",
                )

            except Exception as ex:
                print(f"[ERROR] {ex}")
                pass

# MENU BUTTONS
@app.on_message(filters.text & filters.regex("^Activate$"))
async def active_button(client, message):
    await set_user_active(message.chat.id, 1)
    await set_user_mute(message.chat.id, 0)
    await message.reply_text("Bot activated. You will receive threat alerts.")
    
@app.on_message(filters.text & filters.regex("^Deactivate$"))
async def deactivate_button(client, message):
    await set_user_active(message.chat.id, 0)
    await message.reply_text("Bot deactivated. You will not receive any alerts.")

@app.on_message(filters.text & filters.regex("^Mute$"))
async def mute_button(client, message):
    await set_user_mute(message.chat.id, 1)
    await message.reply_text("Alerts muted. You will not receive notifications until the all-clear signal.")

@app.on_message(filters.text & filters.regex("^Unmute$"))
async def unmute_button(client, message):
    await set_user_mute(message.chat.id, 0)
    await message.reply_text("Alerts unmuted. You will receive all notifications.")

@app.on_message(filters.text & filters.regex("^Status$"))
async def status_button(client, message):
    info = await get_user_info(message.chat.id)

    if info is None:
        await message.reply_text("Error: User not found in the database. Please send /start.")
        return

    await message.reply_text(f"Your status:\nActive: {'+' if info[0] else '-'}\nMuted: {'+' if info[1] else '-'}")

@app.on_message(filters.text & filters.regex("^Info$"))
async def info_button(client, message):
    info_text = (
        "This bot was created as a pet project by @vanago_official.\n\n"
        "It monitors radar channels in real-time and uses Artificial Intelligence "
        "to filter out spam, providing you with immediate alerts ONLY about direct "
        "ballistic or missile threats to your city."
    )
    await message.reply_text(info_text)

async def main():
    await init_db()
    await app.start()
    await userbot.start()
    print("[STATUS] bot is started.")

    global alert_status

    try:
        while True:
            is_alert = await get_alert()

            if is_alert and not alert_status:
                alert_status = True
                print(f"[ALERT] {CITY}")

            elif not is_alert and alert_status:
                print(f"[no alert] {CITY}")
                alert_status = False
                await set_all_mutes(0)

            await asyncio.sleep(60)

    finally:
        await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nBot stoped.")
