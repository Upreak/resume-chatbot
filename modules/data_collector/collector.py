from fastapi import APIRouter, Request
from parser_module.resume_parser import parse_resume_text
from shared.telegram_api import send_message
import json
import os
import httpx

router = APIRouter()

# In-memory data storage (replace with Google Sheets / Firebase in future)
user_profiles = {}
qid_status = {}

# Required fields to match jobs
REQUIRED_FIELDS = ["name", "email", "phone", "skills", "education", "experience", "current_role", "current_location"]

@router.post("/collect")
async def collect_data(request: Request):
    payload = await request.json()

    chat_id = payload["chat_id"]
    qid = payload["qid"]
    source = payload["source"]  # "manual" or "resume"
    data = payload["data"]

    # Resume Parsing
    if source == "resume" and "raw_text" in data:
        # Save raw resume → temp file
        file_path = "/tmp/resume_input.pdf"
        with open(file_path, "w") as f:
            f.write(data["raw_text"])  # for demo; real app = upload path
        structured = parse_resume_text(file_path)
    elif source == "manual":
        structured = data
    else:
        structured = {}

    # Store profile
    user_profiles[chat_id] = structured

    # Check for completeness
    missing_fields = [field for field in REQUIRED_FIELDS if not structured.get(field)]
    if missing_fields:
        qid_status[qid] = {"status": "incomplete", "missing": missing_fields}
        await send_message(chat_id, f"⚠️ Missing info: {', '.join(missing_fields)}\nWe'll ask now...")
        return {"ok": True, "missing": missing_fields}

    # Mark complete and send to center
    qid_status[qid] = {"status": "complete"}

    # 🔁 Call center module to process QID
    async with httpx.AsyncClient() as client:
        await client.post("http://center-module.internal/process", json={
            "chat_id": chat_id,
            "qid": qid,
            "profile": structured
        })

    await send_message(chat_id, "✅ Profile complete! Now processing your request...")
    return {"ok": True, "status": "complete"}
