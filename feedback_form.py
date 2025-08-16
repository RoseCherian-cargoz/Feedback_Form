from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import gspread
import json
import streamlit as st
from datetime import date
import io

# ------------------- Google API Setup -------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
service_account_info = json.loads(st.secrets["google"]["gcp_service_account"])
creds = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=creds)
# service = build('sheets', 'v4', credentials=creds)

#Document Upload-------------------------------
from googleapiclient.errors import HttpError

# SHARED_DRIVE_FOLDER_ID = '0AJ2EMdEDYgIcUk9PVA'  # update this
FOLDER_ID = "0AAOj3djVHPpNUk9PVA?"

def upload_file_to_drive(file, folder_id=FOLDER_ID):
    file_io = io.BytesIO(file.getbuffer())
    file_metadata = {'name': file.name, 'parents': [folder_id]}
    mime_type = file.type if file.type else "application/octet-stream"
    media = MediaIoBaseUpload(file_io, mimetype=mime_type, resumable=True)

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True  # IMPORTANT for shared drives
    ).execute()

    drive_service.permissions().create(
        fileId=uploaded_file['id'],
        body={'type': 'anyone', 'role': 'reader'},
        supportsAllDrives=True  # IMPORTANT
    ).execute()

    return f"https://drive.google.com/file/d/{uploaded_file['id']}/view?usp=sharing"

# Initialize Google Drive and Sheets services
# drive_service = build("drive", "v3", credentials=creds)
SHEET_ID = st.secrets["google"]["sheet_id"]

# ✅ Use your valid Shared Drive folder ID
# FOLDER_ID = st.secrets["google"]["folder_id"]  # should be "1MjK_EDuIs1mBbtSBMacsX9m3OCBbXN6u"

gc = gspread.authorize(creds)
worksheet = gc.open_by_key(SHEET_ID).sheet1

# ------------------- Streamlit Form -------------------
st.title("📋 Product Feedback Submission Form")

poc = st.text_input("POC (Point of Contact)", placeholder="Name of the person responsible")
team = st.text_input("Team", placeholder="e.g., Development, Marketing, Design")
feedback_date = st.date_input("Date", value=date.today())
feedback = st.text_area("Feedback", placeholder="Summarize the feedback here")
description = st.text_area("Description", placeholder="Add more details about the feedback")
product_flow = st.text_input("Which Product / Page / Flow?", placeholder="e.g., Checkout Page, Dashboard, etc.")
reason_impact = st.text_area("What is the reason for implementing it? - Impact", placeholder="Describe the business or user impact")

attachments = st.file_uploader(
    "Reference doc / Screenshots / Images / Data (Attach if needed)",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg", "pdf", "docx", "xlsx"]
)

# ------------------- Submit Action -------------------
if st.button("Submit Feedback"):
    file_links = []

    # Upload files to Google Drive (Shared Drive folder)
    # if attachments:
    #     for file in attachments:
    #         try:
    #             file_metadata = {
    #                 "name": file.name,
    #                 "parents": [FOLDER_ID]
    #             }
    #             # Reset file pointer after .read()
    #             file_content = io.BytesIO(file.getbuffer())
    #             media = MediaIoBaseUpload(file_content, mimetype=file.type or "application/octet-stream")

    #             uploaded_file = drive_service.files().create(
    #                 body=file_metadata,
    #                 media_body=media,
    #                 fields="id",
    #                 supportsAllDrives=True  # ✅ required for Shared Drives
    #             ).execute()

    #             file_link = f"https://drive.google.com/file/d/{uploaded_file['id']}/view"
    #             file_links.append(file_link)
    #         except Exception as e:
    #             st.error(f"❌ Failed to upload {file.name}: {e}")

    # Save submission to Google Sheet
    try:
        worksheet.append_row([
            str(feedback_date),
            poc,
            team,
            feedback,
            description,
            product_flow,
            reason_impact,
            ", ".join(file_links)
        ])
        st.success("✅ Feedback submitted successfully!")
    except Exception as e:
        st.error(f"❌ Failed to save feedback to Google Sheet: {e}")

    # Display submission summary
    st.write("### 📑 Summary of your submission")
    st.write(f"**Feedback:** {feedback}")
    st.write(f"**Description:** {description}")
    st.write(f"**Product/Page/Flow:** {product_flow}")
    st.write(f"**Team:** {team}")
    st.write(f"**POC:** {poc}")
    st.write(f"**Reason & Impact:** {reason_impact}")
    st.write(f"**Date:** {feedback_date}")

    if file_links:
        st.markdown("**📂 Files Uploaded:**")
        for link in file_links:
            st.markdown(f"- [View File]({link})")
