import logging

logger = logging.getLogger(__name__)
import configparser
from os import getenv

from dotenv import load_dotenv

load_dotenv()

import httpx  # pyright: ignore[reportMissingImports]

config = configparser.ConfigParser()
config.read("config.cfg")

token = getenv("ALARM")

ALERT_API = config["Settings"]["ALERT_API"]
CITY = config["Settings"]["CITY"]


async def get_alert():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ALERT_API}{token}")
            data = response.json()

            alerts_list = data.get("alerts", [])
            # Find the alert dict for our specific CITY by location_uid
            city_data = next((a for a in alerts_list if str(a.get("location_uid")) == str(CITY)), None)
            
            if city_data is None:
                return False, None

            threats = city_data.get("threats", [])
            if not threats:
                return False, None

            threat_type = threats[0].get("threat_type")
            is_alert = city_data.get("alert_level")
            return is_alert, threat_type
    except Exception as e:  # noqa: BLE001
        logger.error(f"[API ERROR] Не вдалося перевірити тривогу: {e}")
        return False, None
