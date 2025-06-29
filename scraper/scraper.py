# modules/scraper/scraper.py

from fastapi import APIRouter, Request
import os
import httpx
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from shared.telegram_api import send_message

router = APIRouter()

@router.post("/scrape")
async def scrape_jobs(request: Request):
    payload = await request.json()
    chat_id = payload["chat_id"]
    qid = payload["qid"]
    data = payload["data"]

    try:
        query = build_search_query(data)
        urls = duckduckgo_job_search(query)

        if not urls:
            await send_message(chat_id, "😓 Sorry, couldn't find any matching jobs.")
            return {"ok": False}

        results = []
        for url in urls[:5]:  # limit to 5 results
            job_info = await fetch_job_details(url)
            if job_info:
                results.append(job_info)

        if not results:
            await send_message(chat_id, "🕸️ Found links, but couldn’t read job details.")
            return {"ok": False}

        # ✅ Format and send to user
        msg = "🔍 *Top job matches:*\n\n"
        for job in results:
            msg += f"🔹 *{job['title']}* at {job['company']}\n📍 {job['location']}\n🔗 {job['url']}\n\n"

        await send_message(chat_id, msg)
        return {"ok": True, "count": len(results)}

    except Exception as e:
        print("Scraper error:", e)
        await send_message(chat_id, "❌ An error occurred during job search.")
        return {"ok": False, "error": str(e)}


def build_search_query(data: dict) -> str:
    role = data.get("current_role", "")
    skills = data.get("skills", "")
    loc = data.get("preferred_location", "")
    return f"{role} {skills} jobs in {loc}".strip()


def duckduckgo_job_search(query: str) -> list:
    links = []
    with DDGS() as ddgs:
        for r in ddgs.text(query + " site:linkedin.com OR site:internshala.com OR site:naukri.com", max_results=10):
            links.append(r["href"])
    return links


async def fetch_job_details(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            soup = BeautifulSoup(r.text, "lxml")

        # Very naive title detection
        title = soup.title.string.strip()[:80] if soup.title else "Job Posting"
        return {
            "title": title,
            "company": "Company Name",
            "location": "Unknown",
            "url": url
        }

    except Exception as e:
        print("Error scraping job:", e)
        return None
