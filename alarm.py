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

            city_data = data.get("alerts", {}).get(CITY)
            if city_data is None:
                return False

            threats = city_data.get("threats", [])
            if not threats:
                return False

            return city_data.get("alert_level") == "red" and threats[0].get("threat_type") in {
                "ballistic_missiles",
                "cruise_missiles",
                "unspecified_missiles",
            }
    except Exception as e:  # noqa: BLE001
        logger.error(f"[API ERROR] Не вдалося перевірити тривогу: {e}")
        return False
