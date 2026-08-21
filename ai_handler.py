import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

AI_KEY = os.getenv("AI_KEY") 

import configparser

config = configparser.ConfigParser()
config.read("config.cfg")
CITY = config["Settings"]["CITY"]

SYSTEM_PROMPT = f"""Ти військовий аналітик. Твоя єдина задача — аналізувати вхідні повідомлення з радарів і визначати, чи існує ПРЯМА загроза балістики, крилатих ракет (Х-101, Кинджал, тощо) для міста {CITY}.

ПРАВИЛА:
1. Відповідай СУВОРО одним словом: THREAT або IGNORE. Жодних пояснень чи крапок.
2. Реагуй (THREAT) ЛИШЕ на пряму ракетну або балістичну загрозу безпосередньо для міста {CITY}.
3. Ігноруй (IGNORE) будь-які повідомлення про інші міста, прості зльоти авіації без пусків, рух шахедів, рекламні інтеграції, збори коштів або інформаційні пости.

ПРИКЛАДИ:
Повідомлення: Швидкісна ціль (балістика) курсом на {CITY}, негайно в укриття!
Відповідь: THREAT

Повідомлення: Крилата ракета Х-101 через Сумщину, курс західний.
Відповідь: IGNORE

Повідомлення: Ракета змінила курс, летить на {CITY}!
Відповідь: THREAT

Повідомлення: Увага! Зліт МіГ-31К з аеродрому Саваслейка.
Відповідь: IGNORE

Повідомлення: Група шахедів наближається до Білої Церкви.
Відповідь: IGNORE

Повідомлення: Допоможіть закрити збір на дрони для 3-ї ОШБр!
Відповідь: IGNORE"""

async def analyze_message(text: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-3.1-flash-lite",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logging.error(f"[AI ERROR] OpenRouter API Error: {e}")
            return "IGNORE"