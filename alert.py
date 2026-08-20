import httpx
import configparser

config = configparser.ConfigParser()
config.read("config.cfg")

ALERT_API = config["Settings"]["ALERT_API"]
CITY = config["Settings"]["CITY"]

async def get_alert():
    async with httpx.AsyncClient() as client:
        response = await client.get(ALERT_API)
        data = response.json()

        if data["states"][CITY]["alertnow"]:
            return True
        
        return False

