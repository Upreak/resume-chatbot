import pdfplumber
import re

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def parse_resume_text(text: str) -> dict:
    # Basic patterns
    email = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone = re.findall(r"\+?\d[\d\s\-()]{8,}", text)

    # Try to guess name (first line fallback)
    lines = text.splitlines()
    probable_name = lines[0].strip() if lines else ""

    # Keywords-based skill extraction (simple)
    skill_keywords = ["Python", "Java", "SQL", "HTML", "CSS", "JavaScript", "AWS", "Node.js", "React", "FastAPI"]
    found_skills = [skill for skill in skill_keywords if skill.lower() in text.lower()]

    return {
        "name": probable_name,
        "email": email[0] if email else "Not found",
        "phone": phone[0] if phone else "Not found",
        "skills": found_skills or [],
    }
