# shared/logger.py

from datetime import datetime

def log_event(event: str, data: dict = {}):
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] {event} → {data}")
