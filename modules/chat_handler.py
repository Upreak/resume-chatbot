from fastapi import APIRouter, Request
import httpx
import os

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@router.post("/webhook/telegram")
async def telegram_webhook(req: Request):
    body = await req.json()
    chat_id = body['message']['chat']['id']
    user_message = body['message']['text']

    reply = f"You said: {user_message}"

    send_message_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": reply
    }

    async with httpx.AsyncClient() as client:
        await client.post(send_message_url, json=payload)

    return {"ok": True}
