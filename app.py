from fastapi import FastAPI
from modules.chat_handler import router as telegram_router

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello from FastAPI"}

# Include the Telegram webhook router
app.include_router(telegram_router)
