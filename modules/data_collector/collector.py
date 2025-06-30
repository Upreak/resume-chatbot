from fastapi import APIRouter, Request
from parser_module.resume_parser import parse_resume_text
from shared.telegram_api import send_message
import os
import httpx

router = APIRouter()

# In-memory storage (can replace later with GSheets/Firebase)
user_profiles = {}
qid_status = {}

REQUIRED_FIELDS = [
    "name", "email", "phone", "skills",
    "education", "experience", "current_role", "current_location"
]

# ✅ FastAPI route (optional if called via HTTP)
@router.post("/collect")
async def collect_data(request: Request):
    payload = await request.json()
    chat_id = payload["chat_id"]
    qid = payload["qid"]
    source = payload["source"]  # "resume" or "manual"
    data = payload["data"]
    return await process_profile(chat_id, qid, source, data)

# ✅ Core logic: reusable function for internal calls
async def process_profile(chat_id: str, qid: str, source: str, data: dict):
    # Resume Parsing Logic
    if source == "resume" and "raw_text" in data:
        file_path = "/tmp/resume_input.txt"
        with open(file_path, "w") as f:
            f.write(data["raw_text"])
        structured = parse_resume_text(file_path)
    elif source == "manual":
        structured = data
    else:
        structured = {}

    # Store the structured profile
    user_profiles[chat_id] = structured

    # Check for completeness
    missing_fields = [field for field in REQUIRED_FIELDS if not structured.get(field)]
    if missing_fields:
        qid_status[qid] = {"status": "incomplete", "missing": missing_fields}
        await send_message(chat_id, f"⚠️ Missing info: {', '.join(missing_fields)}\nWe'll ask now...")
        return {"ok": True, "missing": missing_fields}

    # ✅ All data present
    qid_status[qid] = {"status": "complete"}
    await send_message(chat_id, "✅ Profile complete! Now processing your request...")

    # ⏳ Optional: Forward to center module
    try:
        async with httpx.AsyncClient() as client:
            await client.post("http://center-module.internal/process", json={
                "chat_id": chat_id,
                "qid": qid,
                "profile": structured
            })
    except Exception as e:
        print(f"[WARN] Failed to reach center module: {e}")

    return {"ok": True, "status": "complete"}
