# shared/logger.py

from datetime import datetime
import json
import os
import traceback

from shared.config import LOG_TO_SHEETS, LOG_TO_FIREBASE, SHEETS_CREDENTIALS_JSON, SHEET_ID, FIREBASE_CONFIG

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

# Initialize Firebase (once)
firebase_initialized = False

def log_event(event_type: str, payload: dict = {}):
    timestamp = datetime.utcnow().isoformat()

    row = {
        "timestamp": timestamp,
        "event": event_type,
        "data": json.dumps(payload)
    }

    print(f"[LOG] {timestamp} - {event_type} - {payload}")

    if LOG_TO_SHEETS:
        try:
            log_to_sheets(row)
        except Exception as e:
            print(f"[SHEETS_LOG_ERROR] {e}")

    if LOG_TO_FIREBASE:
        try:
            log_to_firebase(row)
        except Exception as e:
            print(f"[FIREBASE_LOG_ERROR] {e}")

def log_to_sheets(row: dict):
    if not gspread:
        raise ImportError("gspread not installed")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(SHEETS_CREDENTIALS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    sheet.append_row([row["timestamp"], row["event"], row["data"]])

def log_to_firebase(row: dict):
    global firebase_initialized
    if not firebase_admin:
        raise ImportError("firebase-admin not installed")

    if not firebase_initialized:
        cred = credentials.Certificate(json.loads(FIREBASE_CONFIG))
        firebase_admin.initialize_app(cred)
        firebase_initialized = True

    db = firestore.client()
    db.collection("logs").add(row)
