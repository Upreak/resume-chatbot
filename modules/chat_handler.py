from fastapi import APIRouter, Request
import httpx
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
router = APIRouter()

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        print("📩 Received:", data)

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            if text:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": f"🧠 Echo: {text}"}
                    )

        return {"ok": True}

    except Exception as e:
        print("❌ Error:", e)
        return {"ok": False}
