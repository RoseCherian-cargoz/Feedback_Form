import streamlit as st
from datetime import date

st.title("📋 Feedback Submission Form")
# 1. POC
poc = st.text_input("POC (Point of Contact)", placeholder="Name of the person responsible")
# 2. Team
team = st.text_input("Team", placeholder="e.g., Development, Marketing, Design")
# 3. Date
feedback_date = st.date_input("Date", value=date.today())
# 4. Feedback
feedback = st.text_area("Feedback", placeholder="Summarize the feedback here")
# 5. Description
description = st.text_area("Description", placeholder="Add more details about the feedback")
# 6. Which Product/page/flow?
product_flow = st.text_input("Which Product / Page / Flow?", placeholder="e.g., Checkout Page, Dashboard, etc.")
# 7. Reason & Impact
reason_impact = st.text_area("What is the reason for implementing it? - Impact", placeholder="Describe the business or user impact")

# 9. Attachments (Screenshots / Images / Data)
attachments = st.file_uploader(
    "Reference doc / Screenshots / Images / Data (Attach if needed)",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg", "pdf", "docx", "xlsx"]
)

# Submit button
if st.button("Submit Feedback"):
    st.success("✅ Feedback submitted successfully!")
    
    st.write("### Summary of your submission")
    st.write(f"**Feedback:** {feedback}")
    st.write(f"**Description:** {description}")
    st.write(f"**Product/Page/Flow:** {product_flow}")
    st.write(f"**Team:** {team}")
    st.write(f"**POC:** {poc}")
    st.write(f"**Reason & Impact:** {reason_impact}")
    st.write(f"**Date:** {feedback_date}")
    if reference_link:
        st.markdown(f"[Reference Document]({reference_link})")
    if attachments:
        st.write(f"Attached Files: {[file.name for file in attachments]}")
