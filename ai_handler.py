import logging
import os
import configparser
from dotenv import load_dotenv
from groq import AsyncGroq

config = configparser.ConfigParser()
config.read("config.cfg")

CITY = config["Settings"]["CITY"]

load_dotenv()
AI_KEY = os.getenv("AI_KEY")

client = AsyncGroq(api_key=AI_KEY)

async def analyze_message(text):
    system_prompt = """Ти військовий аналітик. Твоя єдина задача — аналізувати вхідні повідомлення з радарів і визначати, чи існує ПРЯМА загроза балістики, крилатих ракет (Х-101, Кинджал, тощо) для    
  міста {CITY}.                                                                                                                                                                                               
                                                                                                                                                                                                              
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

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0,
            max_tokens=10
            )
            
        return chat_completion.choices[0].message.content.strip()
            
    except Exception as e:
        logging.error(f"[AI ERROR] {e}")
        return "IGNORE"