from fastapi import FastAPI
from modules.chat_handler import router as telegram_router
from modules.center_module.center_module import router as center_router

app = FastAPI()

# Include the Telegram webhook router
app.include_router(telegram_router)
app.include_router(center_router)
