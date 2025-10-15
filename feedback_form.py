from datetime import date
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json

# ------------------- CONFIG -------------------
SPREADSHEET_ID = "1oqEuvvbHXKyFODImoLnNmy6QlcCxtAXlGe9lD6fDlA0"
SHEET_NAME = "Sheet1"
SHARED_DRIVE_FOLDER_ID = "0AAOj3djVHPpNUk9PVA"  # Shared Drive ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Service account credentials from Streamlit secrets
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["google"]["gcp_service_account"]),
    scopes=SCOPES
)

sheets_service = build("sheets", "v4", credentials=credentials)
drive_service = build("drive", "v3", credentials=credentials)

# ------------------- FUNCTIONS -------------------

def ensure_header():
    """Ensure the header row exists in the Google Sheet."""
    header = [
        "POC", "Team", "Date","Product","Feedback",
        "Description", "Impact", "Attachments"
    ]
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:H1"
    ).execute()
    existing_header = result.get("values", [])
    if not existing_header or existing_header[0] != header:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body={"values": [header]}
        ).execute()


def append_row(data: list):
    """Append a single row of data to the Google Sheet."""
    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [data]}
    ).execute()


def upload_to_drive(uploaded_file):
    """Upload a single Streamlit UploadedFile to Google Shared Drive and return a public link."""
    try:
        file_io = io.BytesIO(uploaded_file.getbuffer())
        file_io.seek(0)
        file_metadata = {
            "name": uploaded_file.name,
            "parents": [SHARED_DRIVE_FOLDER_ID]
        }
        media = MediaIoBaseUpload(file_io, mimetype=uploaded_file.type or "application/octet-stream")
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()
        # Make file public
        drive_service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"},
            supportsAllDrives=True
        ).execute()
        return f"https://drive.google.com/file/d/{file['id']}/view?usp=sharing"
    except Exception as e:
        st.error(f"❌ Failed to upload {uploaded_file.name}: {e}")
        return None

# ------------------- STREAMLIT UI -------------------
st.title("📋 Product Feedback Submission Form")

poc = st.text_input("POC (Point of Contact)", placeholder="Name of the person responsible")
team = st.text_input("Team", placeholder="e.g., Development, Marketing, Design")
feedback_date = st.date_input("Date", value=date.today())
product = st.selectbox(
    "Product",
    [
        "PPC landing page",
        "Thank you webpage",
        "Thank you email",
        "Lead form",
        "Warehouse finder",
        "Warehouse data",
        "Quotation",
        "Quotation sharing with customer",
        "Log note",
        "Email notifications on lead actions"
    ]
)
feedback = st.text_area("Feedback", placeholder="Summarize the feedback here")
description = st.text_area("Description", placeholder="Add more details about the feedback")
# product_flow = st.text_input("Which Product / Page / Flow?", placeholder="e.g., Checkout Page, Dashboard, etc.")
reason_impact = st.text_area("What is the reason for implementing it? - Impact", placeholder="Describe the business or user impact")

attachments = st.file_uploader(
    "Reference doc / Screenshots / Images / Data (Attach if needed)",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg", "pdf", "docx", "xlsx"]
)

# ------------------- SUBMIT -------------------
if st.button("Submit"):
    if not poc or not team or not feedback:
        st.error("⚠️ Please fill at least POC, Team, and Feedback.")
    else:
        try:
            ensure_header()

            # Upload attachments and get Drive links
            if attachments:
                attachment_links = []
                for file in attachments:
                    link = upload_to_drive(file)
                    if link:
                        attachment_links.append(link)
                attachments_str = ", ".join(attachment_links) if attachment_links else "N/A"
            else:
                attachments_str = "N/A"

            row = [
                poc,
                team,
                str(feedback_date),
                product
                feedback,
                description,
                # product_flow,
                reason_impact,
                attachments_str
            ]

            append_row(row)
            st.success("✅ Form submitted successfully and saved to Google Sheets with attachment links!")

        except Exception as e:
            st.error(f"❌ Error: {e}")
