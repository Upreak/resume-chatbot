import os
import httpx

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def send_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
