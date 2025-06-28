import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Path to your service account key JSON
SERVICE_ACCOUNT_FILE = "credentials.json"  # place this in the project root

# Set the Drive folder ID where resumes will be uploaded
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Define scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Authenticate with the service account
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Create Drive API client
drive_service = build("drive", "v3", credentials=credentials)


def upload_pdf_to_drive(file_path, filename):
    file_metadata = {
        "name": filename,
        "parents": [DRIVE_FOLDER_ID]
    }

    media = MediaFileUpload(file_path, mimetype="application/pdf")

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    print("✅ Uploaded to Drive:", file.get("webViewLink"))
    return file

