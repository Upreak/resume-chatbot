from fastapi import APIRouter, Request
import json
import os
import httpx
from shared.telegram_api import send_message

router = APIRouter()

# Load instructions at startup
with open("modules/center_module/instructions.json") as f:
    instructions = json.load(f)

@router.post("/process")
async def process_qid(request: Request):
    payload = await request.json()

    chat_id = payload["chat_id"]
    qid = payload["qid"]
    profile = payload["profile"]

    try:
        qtype = qid.split("-")[0]  # JM, RD, etc.

        if qtype not in instructions:
            await send_message(chat_id, "❌ Unknown request type. Please restart.")
            return {"ok": False, "error": "Invalid QID type"}

        rule = instructions[qtype]
        module = rule["module"]
        fields = rule["params"]

        if fields == "all":
            data_to_send = profile
        else:
            data_to_send = {k: profile.get(k, "") for k in fields}

        # Call the right downstream module
        if module == "scraper":
            async with httpx.AsyncClient() as client:
                resp = await client.post("http://scraper.internal/scrape", json={
                    "chat_id": chat_id,
                    "qid": qid,
                    "data": data_to_send
                })
            if resp.status_code == 200:
                await send_message(chat_id, "📬 We've found job matches for you!")
            else:
                await handle_failure(chat_id, rule["on_fail"])

        elif module == "resume_builder":
            async with httpx.AsyncClient() as client:
                resp = await client.post("http://resume-builder.internal/build", json={
                    "chat_id": chat_id,
                    "qid": qid,
                    "data": data_to_send
                })
            if resp.status_code == 200:
                await send_message(chat_id, "📄 Your resume is ready. Download link will be sent shortly.")
            else:
                await handle_failure(chat_id, rule["on_fail"])

        return {"ok": True, "module": module}

    except Exception as e:
        print("❗ CenterModule Error:", e)
        await handle_failure(chat_id, "technical")
        return {"ok": False, "error": str(e)}

# 🔁 Fail-safe fallback
async def handle_failure(chat_id, fail_code):
    if fail_code == "technical":
        await send_message(chat_id, "⚠️ We're having trouble processing your request. Please try again later.")
    elif fail_code == "manual_review":
        await send_message(chat_id, "📝 We're reviewing your info manually. We'll follow up soon.")
    else:
        await send_message(chat_id, "😵 Something went wrong. Try again later.")
