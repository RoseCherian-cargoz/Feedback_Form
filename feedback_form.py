from datetime import date
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
# ------------------- CONFIG -------------------
SPREADSHEET_ID = "1oqEuvvbHXKyFODImoLnNmy6QlcCxtAXlGe9lD6fDlA0"
SHEET_NAME = "Sheet1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Service account credentials from Streamlit secrets
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["google"]["gcp_service_account"]),
    scopes=SCOPES
)

sheets_service = build("sheets", "v4", credentials=credentials)

# ------------------- FUNCTIONS -------------------
def ensure_header():
    """Ensure the header row exists in the sheet."""
    header = [
        "POC", "Team", "Date", "Feedback",
        "Description", "Product", "Impact", "Attachments"
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


# ------------------- STREAMLIT UI -------------------
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

# ------------------- SUBMIT -------------------
if st.button("Submit"):
    if not poc or not team or not feedback:
        st.error("⚠️ Please fill at least POC, Team, and Feedback.")
    else:
        try:
            # Ensure header exists
            ensure_header()

            # Handle attachments
            if attachments:
                attachment_str = ", ".join([file.name for file in attachments])
            else:
                attachment_str = "N/A"

            # Prepare row
            row = [
                poc,
                team,
                str(feedback_date),
                feedback,
                description,
                product_flow,
                reason_impact,
                attachment_str
            ]

            # Append row to Google Sheet
            append_row(row)

            st.success("✅ Form submitted successfully and saved to Google Sheets!")

        except Exception as e:
            st.error(f"❌ Error: {e}")
