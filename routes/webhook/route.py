import httpx
from fastapi import APIRouter, Query
from config import settings
from fastapi import Request, Response

router = APIRouter(prefix="/webhook", tags=["webhook"])


async def send_whatsapp_message(phone: str, message: str):
    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {"body": message},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
    print(f"WhatsApp send status: {resp.status_code}")


@router.get("/")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_token == settings.WEBHOOK_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")

    return Response(content="Verification failed", status_code=403)


@router.post("/")
async def receive_message(request: Request):
    payload = await request.json()

    try:
        changes = payload["entry"][0]["changes"][0]["value"]

        # Ignore status updates (delivery receipts, read receipts, etc.)
        if "messages" not in changes:
            return Response(content="Event received", status_code=200)

        message = changes["messages"][0]

        # Only handle text messages
        if message.get("type") != "text":
            return Response(content="Event received", status_code=200)

        phone_number = message["from"]
        text = message["text"]["body"]
        sender = changes.get("contacts", [{}])[0].get("profile", {}).get("name")

        agent = request.app.state.agent
        reply = agent.invoke(message=text, phone_number=phone_number, sender=sender)

        await send_whatsapp_message(phone=phone_number, message=reply)

    except (KeyError, IndexError) as e:
        print("Failed to parse webhook payload:", e)

    return Response(content="Event received", status_code=200)