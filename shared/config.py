# shared/config.py

import os

# Where to log
LOG_TO_SHEETS = os.getenv("LOG_TO_SHEETS", "true").lower() == "true"
LOG_TO_FIREBASE = os.getenv("LOG_TO_FIREBASE", "false").lower() == "true"

# Google Sheets (Required if LOG_TO_SHEETS is true)
SHEETS_CREDENTIALS_JSON = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Firebase (Optional)
FIREBASE_CONFIG = os.getenv("FIREBASE_CONFIG", "")
