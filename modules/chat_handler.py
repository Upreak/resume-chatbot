from fastapi import APIRouter, Request
import httpx
import os
import tempfile
import datetime
from shared.telegram_api import send_message
from parser_module.resume_parser import extract_text_from_pdf

router = APIRouter()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Store user state for manual flow
user_sessions = {}

def generate_qid(query_type: str, chat_id: int) -> str:
    today = datetime.datetime.now().strftime("%Y%m%d")
    return f"{query_type}-{chat_id}-{today}"

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("📩 Received:", data)

    if "message" not in data:
        return {"ok": False, "reason": "No message"}

    message = data["message"]
    chat_id = message["chat"]["id"]

    # Start command
    if "text" in message:
        text = message["text"].strip().lower()

        if text in ["/start", "hi", "hello"]:
            await send_message(chat_id, """
👋 Welcome to Joptech — powered by Upreak 💼

Just upload your resume OR answer a few quick questions — and we’ll find job matches for you.

Choose one:
1️⃣ Upload Resume
2️⃣ Fill Manually
            """)
            user_sessions[chat_id] = {"state": "awaiting_choice"}
            return {"ok": True}

        # Handle resume or manual choice
        if chat_id in user_sessions and user_sessions[chat_id]["state"] == "awaiting_choice":
            if "fill" in text:
                user_sessions[chat_id]["state"] = "manual"
                user_sessions[chat_id]["manual_data"] = {}
                user_sessions[chat_id]["qid"] = generate_qid("JM", chat_id)
                await send_message(chat_id, "What’s your full name?")
                return {"ok": True}
            else:
                await send_message(chat_id, "Upload your resume as a PDF file.")
                return {"ok": True}

        # Manual Q&A flow
        if chat_id in user_sessions and user_sessions[chat_id]["state"] == "manual":
            session = user_sessions[chat_id]
            fields = ["name", "email", "phone", "skills", "education", "experience", "current_role", "preferred_location"]
            current_data = session["manual_data"]

            next_field = fields[len(current_data)]
            current_data[next_field] = text

            if len(current_data) == len(fields):
                # Send to DataCollector
                qid = session["qid"]
                async with httpx.AsyncClient() as client:
                    await client.post("http://data-collector.internal/collect", json={
                        "chat_id": chat_id,
                        "qid": qid,
                        "source": "manual",
                        "data": current_data
                    })

                await send_message(chat_id, "✅ Thanks! We're matching jobs for you now...")
                del user_sessions[chat_id]
            else:
                await send_message(chat_id, f"Please enter your {fields[len(current_data)]}")

            return {"ok": True}

    # If document (resume)
    if "document" in message:
        file_id = message["document"]["file_id"]
        async with httpx.AsyncClient() as client:
            file_info = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
            )
            file_path = file_info.json()["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            file_data = await client.get(file_url)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_data.content)
            pdf_path = tmp.name

        # Extract text from resume
        text = extract_text_from_pdf(pdf_path)
        qid = generate_qid("JM", chat_id)

        # Send to DataCollector
        async with httpx.AsyncClient() as client:
            await client.post("http://data-collector.internal/collect", json={
                "chat_id": chat_id,
                "qid": qid,
                "source": "resume",
                "data": {"raw_text": text}
            })

        await send_message(chat_id, "📄 Resume received! Matching jobs for you now...")
        return {"ok": True}

    return {"ok": False, "reason": "Unhandled message type"}
