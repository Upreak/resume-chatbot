from fastapi import APIRouter, Request
import httpx
import os
import asyncio
import tempfile
from datetime import datetime, timedelta

from modules.parser_module.resume_parser import extract_text_from_pdf, parse_resume_text

router = APIRouter()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 🧠 In-memory store for tracking user activity
user_last_seen = {}

# ✅ Welcome message with options
async def send_welcome(chat_id):
    welcome_text = (
        "👋 Hey! Welcome to Joptech — powered by Upreak 💼\n"
        "We’re your job catalysts, here to help you find the right job, fast.\n\n"
        "Just upload your resume or answer a few quick questions — and we’ll show you top job matches with direct links to apply.\n\n"
        "✅ Super easy\n✅ AI-powered\n✅ Totally free\n\n"
        "Let’s find your next opportunity! 🚀"
    )
    await httpx.AsyncClient().post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": welcome_text,
            "reply_markup": {
                "keyboard": [
                    ["📎 Upload Resume", "✍️ Fill Manually"],
                    ["💬 Contact Support"]
                ],
                "resize_keyboard": True
            }
        }
    )

# ✅ Inactivity checker (3 min)
async def check_inactivity(chat_id):
    await asyncio.sleep(180)
    last_time = user_last_seen.get(chat_id)
    if last_time and (datetime.utcnow() - last_time).total_seconds() >= 180:
        await httpx.AsyncClient().post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": (
                    "🎁 First valuable feedback = Reward! (upto Rs.500)\n\n"
                    "💬 Support (WhatsApp only): +91 99013 81877"
                )
            }
        )

# ✅ Main webhook handler
@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("📩 Received:", data)

    if "message" not in data:
        return {"ok": True}

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    # 🕒 Track user activity
    user_last_seen[chat_id] = datetime.utcnow()
    asyncio.create_task(check_inactivity(chat_id))

    # 🟢 /start command
    if text == "/start":
        await send_welcome(chat_id)
        return {"ok": True}

    # ✍️ Manual input handler
    if text == "✍️ Fill Manually":
        await httpx.AsyncClient().post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "Great! What’s your full name?"}
        )
        return {"ok": True}

    # 📎 Resume file handler
    if "document" in message:
        file_id = message["document"]["file_id"]

        async with httpx.AsyncClient() as client:
            # 1. Get file path
            file_resp = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
            )
            file_path = file_resp.json()["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

            # 2. Download file
            file_data = await client.get(file_url)

            # 3. Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_data.content)
                tmp_path = tmp.name

            # 4. Parse PDF
            extracted_text = extract_text_from_pdf(tmp_path)
            parsed = parse_resume_text(extracted_text)

            # 5. Reply with structured info
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"📄 Name: {parsed['name']}\n📧 Email: {parsed['email']}\n📱 Phone: {parsed['phone']}"
                },
            )

        return {"ok": True}

    # 💬 Default echo fallback
    if text:
        await httpx.AsyncClient().post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": f"🧠 Echo: {text}"}
        )

    return {"ok": True"}
