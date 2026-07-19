import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNELS_TO_MONITOR = ["me", "tviy_kyiv", "kiev1", -1003740116044, -1004298960926]
TARGET_WORDS = ["балістик", "циркон", "кинджал", "кинжал", "іскандер", "швидкісн", "ракет"]
CLEAR_WORDS = ["відбій", "чисто", "дорозвідка"]
