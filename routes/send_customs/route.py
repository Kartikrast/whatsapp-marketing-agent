from fastapi import APIRouter
import httpx
from config import settings

router = APIRouter(prefix="/send_customs", tags=["send_customs"])

@router.post("/send")
async def send_customs(message: str, phone: str):
    whatsapp_url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "text": {"body": message}
        }
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {
            "body": message
        }
    }
    async with httpx.AsyncClient() as http_client:
        resp = await http_client.post(whatsapp_url, json=payload, headers=headers)
    print(f"WhatsApp response: {resp.status_code}")
