from datetime import date
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json
import smtplib
from email.message import EmailMessage

# ------------------- EMAIL NOTIFICATION -------------------
def notify_rose(feedback_text, warehouse_name=None):
    msg = EmailMessage()
    msg['Subject'] = "Warehouse Data Feedback Submitted"
    msg['From'] = st.secrets["gmail"]["email"]
    msg['To'] = "rose@cargoz.com"
    content = f"Warehouse Name: {warehouse_name}\n\nFeedback:\n{feedback_text}" if warehouse_name else feedback_text
    msg.set_content(f"A new feedback row has been submitted for Warehouse Data.\n\n{content}")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(st.secrets["gmail"]["email"], st.secrets["gmail"]["app_password"])
        smtp.send_message(msg)

# ------------------- CONFIG -------------------
SPREADSHEET_ID = "1oqEuvvbHXKyFODImoLnNmy6QlcCxtAXlGe9lD6fDlA0"
SHEET_NAME = "Sheet1"
SHARED_DRIVE_FOLDER_ID = "0AAOj3djVHPpNUk9PVA"  # Shared Drive ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

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
        "POC", "Date", "Product","Warehouse Name","Feedback","Attachments", "Partner Team","Partner Team Comments","Data Team Comments"
    ]
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:F1"
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
    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [data]}
    ).execute()

def upload_to_drive(uploaded_file):
    try:
        file_io = io.BytesIO(uploaded_file.getbuffer())
        file_io.seek(0)
        file_metadata = {"name": uploaded_file.name, "parents": [SHARED_DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(file_io, mimetype=uploaded_file.type or "application/octet-stream")
        file = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id", supportsAllDrives=True
        ).execute()
        drive_service.permissions().create(
            fileId=file["id"], body={"type": "anyone", "role": "reader"}, supportsAllDrives=True
        ).execute()
        return f"https://drive.google.com/file/d/{file['id']}/view?usp=sharing"
    except Exception as e:
        st.error(f"❌ Failed to upload {uploaded_file.name}: {e}")
        return None

# ------------------- STREAMLIT UI -------------------
st.title("📋 Feedback Submission Form")

# Basic fields
poc = st.text_input("POC (Point of Contact)", placeholder="Name of the person responsible")
feedback_date = date.today()  # Automatic current date

# Product selection with radio buttons
product_type = st.radio("Select Type", ["Warehouse Data", "Product Feedback"])

if product_type == "Warehouse Data":
    product = "warehouse Data"
    warehouse_name = st.text_input("Warehouse Name", placeholder="Enter warehouse name")
else:
    product = st.selectbox(
        "Select Product",
        [
            "PPC landing page",
            "Thank you webpage",
            "Thank you email",
            "Lead form",
            "Warehouse finder",
            "Quotation",
            "Quotation sharing with customer",
            "Log note",
            "Email notifications on lead actions"
        ]
    )

feedback = st.text_area("Feedback", placeholder="Summarize the feedback here")

attachments = st.file_uploader(
    "Reference doc / Screenshots / Images / Data (Attach if needed)",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg", "pdf", "docx", "xlsx"]
)

# ------------------- SUBMIT -------------------
# ------------------- SUBMIT -------------------
if st.button("Submit"):
    if not poc or not feedback:
        st.error("⚠️ Please fill at least POC and Feedback.")
    else:
        try:
            ensure_header()

            # Upload attachments
            if attachments:
                attachment_links = []
                for file in attachments:
                    link = upload_to_drive(file)
                    if link:
                        attachment_links.append(link)
                attachments_str = ", ".join(attachment_links) if attachment_links else "N/A"
            else:
                attachments_str = "N/A"

            # Partner Team logic based on radio button
            if product_type == "Warehouse Data":
                partner_team_flag = "Yes - @rose@cargoz.com"
                  # Pass the feedback text to email
                notify_rose(feedback,warehouse_name)
            else:
                partner_team_flag = "N/A"

            row = [
                poc,
                str(feedback_date),
                product,
                warehouse_name if product_type == "Warehouse Data" else "N/A",  
                feedback,
                attachments_str,
                partner_team_flag,
                "",
                "",
            ]
            append_row(row)
            st.success("✅ Form submitted successfully and saved to Google Sheets with attachment links!")

        except Exception as e:
            st.error(f"❌ Error: {e}")

