import fitz  # PyMuPDF
import re
import nltk
nltk.data.path.append("./nltk_data")  # 👈 Add this right after importing nltk

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def parse_resume_text(text: str) -> dict:
    # Example parsing logic — can be improved
    name_match = re.search(r"(?i)name[:\s]*(.*)", text)
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone_match = re.search(r"(\+?\d[\d\s\-\(\)]{9,}\d)", text)

    return {
        "name": name_match.group(1).strip() if name_match else None,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "raw_text": text  # for debugging, remove later
    }
