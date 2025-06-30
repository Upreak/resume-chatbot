import re
import spacy
import pdfplumber

nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def extract_name(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "Unknown"

def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group(0) if match else "Not found"

def extract_phone(text):
    match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{4,6}[-.\s]?\d{0,6}', text)
    return match.group(0) if match else "Not found"

def extract_skills(text):
    SKILLS = ["Python", "JavaScript", "SQL", "AWS", "Django", "React", "Excel", "Java", "C++"]
    return [skill for skill in SKILLS if skill.lower() in text.lower()]

def extract_education(text):
    edu_keywords = ["Bachelor", "Master", "B.Tech", "M.Tech", "B.Sc", "M.Sc", "MBA"]
    lines = text.split("\n")
    for line in lines:
        if any(k in line for k in edu_keywords):
            return line.strip()
    return "Not found"

def extract_experience(text):
    match = re.search(r'(\d+)\+?\s*(years|yrs)', text.lower())
    return match.group(0) if match else "Not found"

def extract_current_role(text):
    for line in text.split("\n")[:10]:  # Only top 10 lines
        if "engineer" in line.lower() or "developer" in line.lower():
            return line.strip()
    return "Not found"

def extract_location(text):
    LOCATIONS = ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Remote"]
    for loc in LOCATIONS:
        if loc.lower() in text.lower():
            return loc
    return "Unknown"

def parse_resume_text(pdf_path: str) -> dict:
    text = extract_text_from_pdf(pdf_path)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "current_role": extract_current_role(text),
        "current_location": extract_location(text),
        "raw_text": text
    }
