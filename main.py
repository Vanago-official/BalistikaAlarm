import asyncio
import logging
from os import getenv

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from alarm import get_alert
from database import (
    add_user,
    get_active_users,
    get_muted_users,
    get_user_info,
    init_db,
    set_all_mutes,
    set_user_active,
    set_user_mute,
)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

BOT_TOKEN = getenv("BOT_TOKEN")

alert_status = False

bot = Bot(BOT_TOKEN)
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
        "👋 Hi! I monitor direct missile threats to Kyiv.\n\nUse the buttons below to control the bot:",
        reply_markup=replyKeyboard,
    )


# MENU BUTTONS
@dp.message(F.text.regexp(r"^✅ Activate$"))
async def active_button(message):
    await set_user_active(message.from_user.id, 1)
    await set_user_mute(message.from_user.id, 0)
    await message.answer("✅ Bot activated. Alerts enabled.", reply_markup=replyKeyboard)


@dp.message(F.text.regexp(r"^🛑 Deactivate$"))
async def deactivate_button(message):
    await set_user_active(message.from_user.id, 0)
    await message.answer("🛑 Bot deactivated. Alerts disabled.", reply_markup=replyKeyboard)


@dp.message(F.text.regexp(r"^🔕 Mute$"))
async def mute_button(message):
    await set_user_mute(message.from_user.id, 1)
    await message.answer("🔕 Alerts muted until all-clear.", reply_markup=replyKeyboard)


@dp.message(F.text.regexp(r"^🔔 Unmute$"))
async def unmute_button(message):
    await set_user_mute(message.from_user.id, 0)
    await message.answer("🔔 Alerts unmuted.", reply_markup=replyKeyboard)


@dp.message(F.text.regexp(r"^📊 Status$"))
async def status_button(message):
    info = await get_user_info(message.from_user.id)

    if info is None:
        await message.answer("⚠️ User not found. Send /start to register.")
        return

    await message.answer(
        f"📊 *Current Status:*\n\n"
        f"🚨 *Air Alert:* {'🔴 Active' if alert_status else '🟢 Inactive'}\n"
        f"✅ *Active:* {'Yes' if info[0] else 'No'}\n"
        f"🔕 *Muted:* {'Yes' if info[1] else 'No'}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=replyKeyboard,
    )


@dp.message(F.text.regexp(r"^ℹ️ Info$"))
async def info_button(message):
    info_text = (
        "Created by @vanago_official.\n\n"
        "Monitors official air alert data in real-time and sends instant notifications "
        "about direct missile threats to Kyiv."
    )
    await message.answer(info_text, reply_markup=replyKeyboard)


async def alert_loop():
    global alert_status
    while True:
        try:
            is_alert, threat_type = await get_alert()
            logger.info(f"[ALERT] {is_alert} - {threat_type}")

            # New threat alert detected
            if is_alert == "red" and not alert_status:
                users = await get_active_users()
                await set_all_mutes(1)

                for user in users:
                    try:
                        await bot.send_message(chat_id=user, text="🔴 Danger!")
                        await asyncio.sleep(0.05)
                    except Exception as e:  # noqa: BLE001
                        logger.error(
                            f"[BOT ERROR] Failed to send message to user {user}: {e}"
                        )

            # Threat alert ended
            elif not is_alert and alert_status:
                users = await get_muted_users()
                await set_all_mutes(0)

                for user in users:
                    try:
                        await bot.send_message(chat_id=user, text="🟢 Clear.")
                        await asyncio.sleep(0.05)
                    except Exception as e:  # noqa: BLE001
                        logger.error(
                            f"[BOT ERROR] Failed to send message to user {user}: {e}"
                        )

            alert_status = is_alert == "red"

        except Exception as e:  # noqa: BLE001
            logger.error(f"[ALERT LOOP ERROR]: {e}")

        await asyncio.sleep(10)


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
        logger.info("Bot stopped.")
