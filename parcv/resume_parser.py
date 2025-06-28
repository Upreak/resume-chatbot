from parcv import parcv

def parse_resume_text(file_path: str) -> dict:
    parser = parcv.Parser(pickle=True, load_pickled=True)
    data = parser.parse(file_path)

    return {
        "full_name": data.get("name", "Not found"),
        "email": data.get("email", "Not found"),
        "phone": data.get("phone", "Not found"),
        "skills": data.get("skills", []),
        "education_highest": data.get("education", [None])[0],
        "education_second": data.get("education", [None, None])[1] if len(data.get("education", [])) > 1 else "",
        "total_experience": data.get("total_experience", "Not found"),
        "current_role": data.get("job_title", "Not found"),
        "current_location": data.get("location", "Not found")
    }

