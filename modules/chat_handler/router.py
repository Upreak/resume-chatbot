from fastapi import APIRouter, Request
import httpx

router = APIRouter()

# Replace with your real bot token
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"

@router.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    
    message_text = data.get("message", {}).get("text", "")
    chat_id = data.get("message", {}).get("chat", {}).get("id")

    if not message_text or not chat_id:
        return {"ok": False, "message": "Invalid Telegram data"}

    # For now, reply with a simple confirmation
    await send_message(chat_id, "✅ Message received! Processing...")

    # TODO: Pass to center_module (we’ll do this after its setup)
    return {"ok": True}


async def send_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

