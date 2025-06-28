from fastapi import APIRouter, Request
import httpx
import os
import asyncio
from datetime import datetime
import re
import nltk
import spacy
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pyresparser import ResumeParser

router = APIRouter()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google Sheets setup
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
GS_CLIENT = gspread.authorize(CREDS)
SHEET = GS_CLIENT.open("Joptech_ResumeData")

# In-memory user sessions
user_last_seen = {}
manual_sessions = {}
correction_sessions = {}

# NLP & pyresparser setup
nltk.download("stopwords")
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")
spacy.cli.download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")

QUESTION_FLOW = [
    "👤 What's your full name?",
    "📧 What's your email?",
    "📱 Your phone number?",
    "🎓 Your highest degree?",
    "📍 Your current location?",
    "🧠 List your top 5 skills (comma-separated)",
    "💼 Your current job title?",
    "📅 How many years of experience do you have?"
]

CORRECTION_FIELDS = ["name", "email", "phone", "education", "skills", "total_experience", "current_role", "current_location"]

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()

async def send_welcome(chat_id):
    text = (
        "👋 Hey! Welcome to Joptech — powered by Upreak 💼\n"
        "We’re your job catalysts, here to help you find the right job, fast.\n\n"
        "Just upload your resume or answer a few quick questions — "
        "and we’ll show you top job matches with direct links to apply.\n\n"
        "✅ Super easy\n✅ AI-powered\n✅ Totally free\n\n"
        "Let’s find your next opportunity! 🚀"
    )
    await httpx.AsyncClient().post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "reply_markup": {
                "keyboard": [
                    ["📎 Upload Resume", "✍️ Fill Manually"],
                    ["💬 Contact Support"]
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
        }
    )

async def check_inactivity(chat_id):
    await asyncio.sleep(180)
    last = user_last_seen.get(chat_id)
    if last and (datetime.utcnow() - last).total_seconds() >= 180:
        await httpx.AsyncClient().post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "🎁 First valuable feedback = Reward! (upto Rs.500)\n\n💬 Support (WhatsApp): +91 99013 81877"}
        )

def save_to_sheet(sheet_name, headers, data):
    try:
        sheet = SHEET.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        sheet = SHEET.add_worksheet(sheet_name, rows="1000", cols=str(len(headers)))
        sheet.append_row(headers)
    sheet.append_row(data)

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    if "message" not in data:
        return {"ok": True}
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    user_last_seen[chat_id] = datetime.utcnow()
    asyncio.create_task(check_inactivity(chat_id))

    if text == "/start":
        await send_welcome(chat_id)
        return {"ok": True}

    # Contact support
    if text == "💬 Contact Support":
        await httpx.AsyncClient().post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": "📱 WhatsApp: +91 99013 81877\n📧 support@upreak.com"}
        )
        return {"ok": True}

    # Manual form
    if text == "✍️ Fill Manually":
        manual_sessions[chat_id] = {"step": 0, "data": {}}
        await httpx.AsyncClient().post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": QUESTION_FLOW[0]}
        )
        return {"ok": True}

    if chat_id in manual_sessions:
        session = manual_sessions[chat_id]
        session["data"][QUESTION_FLOW[session["step"]]] = text
        session["step"] += 1
        if session["step"] < len(QUESTION_FLOW):
            await httpx.AsyncClient().post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": QUESTION_FLOW[session["step"]]}
            )
        else:
            await httpx.AsyncClient().post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": "✅ Thanks! Sending your data for job matching..."}
            )
            headers = ["chat_id"] + QUESTION_FLOW
            row = [chat_id] + list(session["data"].values())
            save_to_sheet("Manual_Entries", headers, row)
            del manual_sessions[chat_id]
        return {"ok": True}

    # Resume upload
    if "document" in msg:
        file_id = msg["document"]["file_id"]
        resp = await httpx.AsyncClient().get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}")
        file_path = resp.json()["result"]["file_path"]
        pdf = await httpx.AsyncClient().get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}")
        with open(f"/tmp/{file_id}.pdf", "wb") as f:
            f.write(pdf.content)

        data = ResumeParser(f"/tmp/{file_id}.pdf").get_extracted_data()
        parsed = {
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "phone": data.get("mobile_number", ""),
            "education": ", ".join(data.get("degree", [])),
            "skills": ", ".join(data.get("skills", [])),
            "total_experience": data.get("total_experience", ""),
            "current_role": data.get("designation", ""),
            "current_location": data.get("location", "")
        }

        correction_sessions[chat_id] = {"original": parsed, "corrected": {}, "step": 0}
        field = CORRECTION_FIELDS[0]
        await httpx.AsyncClient().post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": f"Is this your {field.replace('_', ' ')}?\n➡️ *{parsed[field]}*",
                  "parse_mode": "Markdown",
                  "reply_markup": {"keyboard": [["✅ Yes", "❌ No"]], "resize_keyboard": True}}
        )
        return {"ok": True}

    # Correction flow
    if chat_id in correction_sessions:
        session = correction_sessions[chat_id]
        step = session["step"]
        field = CORRECTION_FIELDS[step]
        if text == "✅ Yes":
            session["corrected"][field] = session["original"][field]
        elif text == "❌ No":
            await httpx.AsyncClient().post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": f"❓ Please enter your correct {field.replace('_', ' ')}:"}
            )
            session["awaiting_correction"] = field
            return {"ok": True}
        elif session.get("awaiting_correction") == field:
            session["corrected"][field] = text
            del session["awaiting_correction"]
        else:
            session["corrected"][field] = session["original"][field]

        session["step"] += 1
        if session["step"] < len(CORRECTION_FIELDS):
            next_f = CORRECTION_FIELDS[session["step"]]
            await httpx.AsyncClient().post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id,
                      "text": f"Is this your {next_f.replace('_', ' ')}?\n➡️ *{session['original'][next_f]}*",
                      "parse_mode": "Markdown",
                      "reply_markup": {"keyboard": [["✅ Yes", "❌ No"]], "resize_keyboard": True}}
            )
        else:
            headers = ["chat_id"] + CORRECTION_FIELDS
            row = [chat_id] + [session["corrected"].get(f, "") for f in CORRECTION_FIELDS]
            save_to_sheet("Corrected_Resumes", headers, row)
            del correction_sessions[chat_id]

            await httpx.AsyncClient().post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": "✅ Thanks! Your verified data is being matched with top jobs..."}
            )
            # Notify center_module:
            # await httpx.AsyncClient().post("https://center.example.com/match", json=session["corrected"])

        return {"ok": True}

    return {"ok": True}
