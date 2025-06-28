from fastapi import FastAPI
from modules.chat_handler import router as telegram_router

app = FastAPI()

# Include the Telegram webhook router
app.include_router(telegram_router)
