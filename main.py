import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
import asyncio
import configparser
from os import getenv

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from alarm import get_alert
from database import *

API_ID = getenv("API_ID")

config = configparser.ConfigParser()
config.read("config.cfg")

alert_status = False

bot = Bot(f"{API_ID}")
dp = Dispatcher()

replyKeyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Activate"),
            KeyboardButton(text="🛑 Deactivate"),
        ],
        [
            KeyboardButton(text="🔕 Mute"),
            KeyboardButton(text="🔔 Unmute"),
        ],
        [
            KeyboardButton(text="📊 Status"),
            KeyboardButton(text="ℹ️ Info"),
        ],
    ],
    resize_keyboard=True,
)


@dp.message(CommandStart())
async def command_start_handler(message):
    await add_user(message.from_user.id)

    await message.answer(
        "👋 Hi! I'm a bot that lets you monitor direct ballistic missile threats to the city of Kyiv.\n\n👇 Use the buttons below to control the bot:", reply_markup=replyKeyboard
    )


# MENU BUTTONS
@dp.message(F.text.regexp(r"^✅ Activate$"))
async def active_button(message):
    await set_user_active(message.from_user.id, 1)
    await set_user_mute(message.from_user.id, 0)
    await message.answer("✅ Bot activated. You will now receive threat alerts.", reply_markup=replyKeyboard)


@dp.message(F.text.regexp(r"^🛑 Deactivate$"))
async def deactivate_button(message):
    await set_user_active(message.from_user.id, 0)
    await message.answer("🛑 Bot deactivated. You will no longer receive any alerts.", reply_markup=replyKeyboard)


@dp.message(F.text.regexp(r"^🔕 Mute$"))
async def mute_button(message):
    await set_user_mute(message.from_user.id, 1)
    await message.answer(
        "🔕 Alerts muted. You will not receive notifications until the all-clear signal.", reply_markup=replyKeyboard
    )


@dp.message(F.text.regexp(r"^🔔 Unmute$"))
async def unmute_button(message):
    await set_user_mute(message.from_user.id, 0)
    await message.answer("🔔 Alerts unmuted. You will receive all notifications.", reply_markup=replyKeyboard)


@dp.message(F.text.regexp(r"^📊 Status$"))
async def status_button(message):
    info = await get_user_info(message.from_user.id)

    if info is None:
        await message.answer(
            "⚠️ Error: User not found in the database. Please send /start."
        )
        return

    await message.answer(
        f"📊 **Current Status:**\n\n"
        f"🚨 **Air Alert:** {'🔴 Active' if alert_status else '🟢 Inactive'}\n"
        f"✅ **Activated:** {'Yes' if info[0] else 'No'}\n"
        f"🔕 **Muted:** {'Yes' if info[1] else 'No'}",parse_mode=ParseMode.MARKDOWN
        , reply_markup=replyKeyboard
    )


@dp.message(F.text.regexp("^ℹ️ Info$"))
async def info_button(message):
    info_text = (
        "This bot was created as a pet project by @vanago_official. "
        "It monitors radar channels in real-time and uses Artificial Intelligence "
        "to filter out spam, providing you with immediate alerts ONLY about direct "
        "ballistic or missile threats to your city."

    )
    await message.answer(info_text, reply_markup=replyKeyboard)


async def alert_loop():
    global alert_status
    try:
        while True:
            is_alert = await get_alert()

            # Якщо почилась тривога і не було
            if is_alert and not alert_status:
                users = await get_active_users()
                await set_all_mutes(1)

                for user in users:
                    try:
                        await bot.send_message(chat_id=user, text="🔴 Danger!")
                        await asyncio.sleep(0.05)
                    except Exception as e:  # noqa: BLE001
                        logger.error(
                            f"[BOT ERROR] Сталася помилка при відправленні повідомлення користувачу {user}: {e}"
                        )

            # Якщо тривога кінчилась
            elif not is_alert and alert_status:
                users = await get_muted_users()
                await set_all_mutes(0)

                for user in users:
                    try:
                        await bot.send_message(chat_id=user, text="🟢 Clear.")
                        await asyncio.sleep(0.05)
                    except Exception as e:  # noqa: BLE001
                        logger.error(
                            f"[BOT ERROR] Сталася помилка при відправленні повідомлення користувачу {user}: {e}"
                        )

            alert_status = is_alert
            await asyncio.sleep(10)

    except Exception as e:  # noqa: BLE001
        logger.error(f"[BOT ERROR]: {e}")
        return False

    finally:
        await dp.stop_polling()

@dp.startup()
async def on_startup():
    await init_db()
    asyncio.create_task(alert_loop())
    logger.info("[STATUS] Bot started.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nBot stoped.")
