# shared/logger.py

from datetime import datetime
import json
import os

from shared.config import (
    LOG_TO_SHEETS,
    LOG_TO_FIREBASE,
    SHEETS_CREDENTIALS_JSON,
    SHEET_ID,
    FIREBASE_CONFIG,
)

# Optional imports
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    gspread = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None

# Internal flag to avoid re-initializing Firebase
firebase_initialized = False


def log_event(event_type: str, payload: dict = {}):
    """Logs an event with timestamp, event type, and payload to console, Google Sheets, and/or Firebase."""
    timestamp = datetime.utcnow().isoformat()

    row = {
        "timestamp": timestamp,
        "event": event_type,
        "data": json.dumps(payload),
    }

    # Print to console
    print(f"[LOG] {timestamp} - {event_type} - {payload}")

    # Log to Google Sheets
    if LOG_TO_SHEETS:
        try:
            log_to_sheets(row)
        except Exception as e:
            print(f"[SHEETS_LOG_ERROR] {e}")

    # Log to Firebase
    if LOG_TO_FIREBASE:
        try:
            log_to_firebase(row)
        except Exception as e:
            print(f"[FIREBASE_LOG_ERROR] {e}")


def log_to_sheets(row: dict):
    if not gspread:
        raise ImportError("gspread is not installed or available.")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = json.loads(SHEETS_CREDENTIALS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    sheet.append_row([row["timestamp"], row["event"], row["data"]])


def log_to_firebase(row: dict):
    global firebase_initialized
    if not firebase_admin:
        raise ImportError("firebase-admin is not installed or available.")

    if not firebase_initialized:
        cred = credentials.Certificate(json.loads(FIREBASE_CONFIG))
        firebase_admin.initialize_app(cred)
        firebase_initialized = True

    db = firestore.client()
    db.collection("logs").add(row)


# Optional local test runner
if __name__ == "__main__":
    log_event("manual_test", {"status": "Logger works ✅"})
