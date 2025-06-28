from resume_parser import resumeparse

def extract_text_from_pdf(file_path: str) -> str:
    # Keep this in case you want raw text
    data = resumeparse.read_file(file_path)
    return data.get("text", "")

def parse_resume_text(file_path: str) -> dict:
    data = resumeparse.read_file(file_path)

    return {
        "full_name": data.get("name", "Not found"),
        "email": data.get("email", "Not found"),
        "phone": data.get("mobile_number", "Not found"),
        "skills": data.get("skills", []),
        "education_highest": data.get("degree", ["Not found"])[0],
        "education_second": data.get("degree", ["", "Not found"])[1] if len(data.get("degree", [])) > 1 else "",
        "total_experience": data.get("total_experience", "Not found"),
        "current_role": data.get("designation", "Not found"),
        "current_location": data.get("location", "Not found")
    }
