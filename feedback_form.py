import streamlit as st
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json

# ------------------- Google API Setup -------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
service_account_info = json.loads(st.secrets["google"]["service_account_json"])
creds = Credentials.from_service_account_file(
    "C:/Users/rose/Documents/VS code scripts/Product feedback form/feeback-form-integration-884b6f0a5709.json",
    scopes=SCOPES)

# Google Sheets setup
SHEET_ID = st.secrets["google"]["sheet_id"]  # Add this in Secrets
gc = gspread.authorize(creds)
worksheet = gc.open_by_key(SHEET_ID).sheet1

# Google Drive setup
FOLDER_ID = st.secrets["google"]["folder_id"]  # Add this in Secrets
drive_service = build("drive", "v3", credentials=creds)

# ------------------- Streamlit Form -------------------
st.title("📋 Product Feedback Submission Form")

# Form fields
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

    # Upload files to Google Drive
    if attachments:
        for file in attachments:
            file_metadata = {
                "name": file.name,
                "parents": [FOLDER_ID]
            }
            media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.type)
            uploaded_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            file_id = uploaded_file.get("id")
            file_link = f"https://drive.google.com/file/d/{file_id}/view"
            file_links.append(file_link)

    # Save submission to Google Sheet
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

    # Success message & summary
    st.success("✅ Feedback submitted successfully!")
    st.write("### Summary of your submission")
    st.write(f"**Feedback:** {feedback}")
    st.write(f"**Description:** {description}")
    st.write(f"**Product/Page/Flow:** {product_flow}")
    st.write(f"**Team:** {team}")
    st.write(f"**POC:** {poc}")
    st.write(f"**Reason & Impact:** {reason_impact}")
    st.write(f"**Date:** {feedback_date}")
    if file_links:
        st.markdown("**Files Uploaded:**")
        for link in file_links:
            st.markdown(f"[View File]({link})")
