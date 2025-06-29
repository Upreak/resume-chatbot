# modules/center_module/center_module.py

from fastapi import APIRouter, Request
import os
import httpx
from shared.logger import log_event
from shared.telegram_api import send_message

router = APIRouter()

# URL of your scraper module (Render base + route)
SCRAPER_URL = os.getenv("SCRAPER_URL", "http://localhost:10000/scrape")

@router.post("/center")
async def center_handler(request: Request):
    payload = await request.json()
    qid = payload["qid"]
    chat_id = payload["chat_id"]
    user_data = payload["data"]

    try:
        query_type = qid.split("-")[0]

        if query_type == "JM":
            # Trigger job matching via Scraper
            resp = await call_scraper(chat_id, qid, user_data)

            if resp and resp.get("ok"):
                return {"ok": True, "status": "job_match_complete"}
            else:
                await send_message(chat_id, "⚠️ Job search failed. Please try again later.")
                return {"ok": False}

        elif query_type == "RD":
            # Later: Trigger ResumeBuilder module
            return {"ok": False, "message": "Resume builder not connected yet."}

        else:
            await send_message(chat_id, "🤖 Unknown QID type.")
            return {"ok": False}

    except Exception as e:
        log_event("CenterModule error", str(e))
        await send_message(chat_id, "❌ Error in processing your request.")
        return {"ok": False, "error": str(e)}


async def call_scraper(chat_id: int, qid: str, user_data: dict) -> dict:
    payload = {
        "chat_id": chat_id,
        "qid": qid,
        "data": user_data
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(SCRAPER_URL, json=payload)
            return r.json()

    except Exception as e:
        log_event("Scraper call failed", str(e))
        return {"ok": False, "error": str(e)}
