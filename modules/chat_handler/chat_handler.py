from fastapi import APIRouter, Request
import httpx
import os

router = APIRouter()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@router.post("/")
async def telegram_webhook(req: Request):
    body = await req.json()
    message = body.get("message", {}).get("text", "")
    chat_id = body.get("message", {}).get("chat", {}).get("id")

    if not message or not chat_id:
        return {"ok": False}

    reply = f"🧠 Echo: {message}"  # You can customize this or connect AI later

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": reply}

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

    return {"ok": True}
