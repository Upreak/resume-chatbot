import pdfplumber
import re
from typing import Dict
from pyresparser import ResumeParser
import nltk

# NLTK path for offline/cloud use
nltk.data.path.append("./nltk_data")

# ✂️ PDF to plain text
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

# 🧠 Fallback name if parser fails
def fallback_name(email: str) -> str:
    if email and "@" in email:
        return email.split("@")[0].replace('.', ' ').title()
    return "Unknown"

# 🧪 Full parser output
def parse_resume_text(file_path: str) -> Dict[str, str]:
    data = ResumeParser(file_path).get_extracted_data()

    # Name fallback
    name = data.get("name") or fallback_name(data.get("email", ""))
    if "father" in name.lower() or "s/o" in name.lower():
        name = fallback_name(data.get("email", ""))

    degrees = data.get("degree", [])
    education_highest = degrees[0] if degrees else "Not found"
    education_second = degrees[1] if len(degrees) > 1 else ""

    result = {
        "name": name,
        "email": data.get("email", "Not found"),
        "phone": data.get("mobile_number", "Not found"),
        "education": f"{education_highest}, {education_second}".strip(", "),
        "skills": ", ".join(data.get("skills", [])),
        "experience": data.get("total_experience", "Not found"),
        "current_role": data.get("designation", "Not found"),
        "current_location": data.get("location", "Not found")
    }

    return result
