from fastapi import APIRouter, Request
import httpx
import os
import tempfile
from modules.parser_module import parser  # 👈 Import parser

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

            # Get file path from Telegram API
            async with httpx.AsyncClient() as client:
                file_resp = await client.get(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
                )
                file_path = file_resp.json()["result"]["file_path"]

                file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                file_data = await client.get(file_url)

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file_data.content)
                    tmp_path = tmp.name

            # Parse and send response
            extracted_text = parser.extract_text_from_pdf(tmp_path)
            preview = extracted_text[:400]  # Limit reply size
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": f"🧾 Extracted Text:\n{preview}"},
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
