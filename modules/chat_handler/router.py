from fastapi import APIRouter, Request
import httpx
import os

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@router.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")

    # ✅ Text message handling
    if "text" in message:
        user_message = message["text"]
        reply = f"🧠 Echo: {user_message}"
        await send_message(chat_id, reply)

    # ✅ File/document upload handling (PDF, DOCX, etc.)
    elif "document" in message:
        file_id = message["document"]["file_id"]
        file_name = message["document"]["file_name"]
        file_url = await get_file_url(file_id)
        reply = f"📄 Received your file: {file_name}\n🧠 Download link: {file_url}\n(Resume parsing will come next!)"
        await send_message(chat_id, reply)

    else:
        await send_message(chat_id, "🤖 Sorry, I didn't understand that input.")

    return {"ok": True}

async def send_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

async def get_file_url(file_id: str) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}")
        file_path = res.json()["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
