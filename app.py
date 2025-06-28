from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Resume Chatbot API is running!"}
