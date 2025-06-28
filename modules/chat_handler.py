from fastapi import APIRouter, Request
import httpx
import os
import tempfile
from modules.parser_module import parser  # 👈 For text extraction
from modules.parser_module.resume_parser import extract_text_from_pdf, parse_resume_text

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
router = APIRouter()

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("📩 Received:", data)

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]

        # 📎 Case: Resume File Sent
        if "document" in message:
            file_id = message["document"]["file_id"]

            async with httpx.AsyncClient() as client:
                # 1. Get file path from Telegram
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

        # 💬 Case: Plain Text
        elif "text" in message:
            text = message["text"]
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": f"🧠 Echo: {text}"},
                )

    return {"ok": True}
