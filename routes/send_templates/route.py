"""
This is the webhook route for the whatsapp marketing api
"""
from fastapi import APIRouter
import httpx
from config import settings

router = APIRouter(prefix="/send_template", tags=["send_template"])


"""
curl -i -X POST `
  https://graph.facebook.com/v22.0/728845600321709/messages `
  -H 'Authorization: Bearer <access token>' `
  -H 'Content-Type: application/json' `
  -d '{ \"messaging_product\": \"whatsapp\", \"to\": \"917409300618\", \"type\": \"template\", \"template\": { \"name\": \"hello_world\", \"language\": { \"code\": \"en_US\" } } }'
"""
       
@router.post("/")
async def send_template(name: str, phone: str):
    url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                    "name": "hello_world",  # your template name
                    "language": {"code": "en_US"}
                }
            }
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            return resp.json()