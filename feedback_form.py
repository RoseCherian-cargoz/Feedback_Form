import io
from datetime import date

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError


# ------------------- UI -------------------
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

# ------------------- Submit Button -------------------
if st.button("Submit"):
    if not poc or not team or not feedback:
        st.error("⚠️ Please fill at least POC, Team, and Feedback.")
    else:
        st.success("✅ Form submitted successfully!")