import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
import asyncio

# Configuration
MAILGUN_DOMAIN = "evertechcms.in"
MAILGUN_FROM = "Ever CMS <mailgun@evertechcms.in>"

# API Key Checker
def check_api_key(user_key):
    valid_keys = [
        st.secrets["api_keys"].get("key_1"),
        st.secrets["api_keys"].get("key_2"),
        st.secrets["api_keys"].get("key_3"),
        st.secrets["api_keys"].get("key_4"),
        st.secrets["api_keys"].get("key_5")
    ]
    return user_key in valid_keys

# Fetch SEBI Guidelines
def fetch_sebi_guidelines():
    url = "https://www.sebi.gov.in/sebi_data/commondocs/cirmf42000_h.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()

# Basic AI Compliance Check (can be expanded with LLM)
def check_compliance(html_content, sebi_text):
    issues = []
    html_lower = html_content.lower()

    if "guarantee" in html_lower or "guaranteed return" in html_lower:
        issues.append("Avoid guaranteeing returns without reserves or third-party backing.")
    if "forecast" in html_lower or "future returns" in html_lower:
        issues.append("Avoid forecasting NAV or performance.")
    if "%" in html_lower and ("return" in html_lower or "growth" in html_lower):
        issues.append("Verify and clarify any percentage returns mentioned.")
    if "best fund" in html_lower or "number one" in html_lower:
        issues.append("Avoid exaggerated/unsubstantiated comparisons.")
    # Add more checks as needed based on full SEBI policy

    return issues

# Email Sending
def send_email(to_email, subject, html_content, api_key):
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", api_key),
            data={
                "from": MAILGUN_FROM,
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send email to {to_email}: {e}")
        return False

# Translation
async def translate_text(text, target_language):
    translator = Translator()
    try:
        translation = await translator.translate(text, dest=target_language)
        return translation.text
    except Exception as e:
        st.error(f"Translation error: {e}")
        return text

# Streamlit UI
user_key = st.text_input("Enter your API key:", type="password")

if user_key:
    if not check_api_key(user_key):
        st.error("Invalid API Key! Access Denied.")
    else:
        st.title("AI Powered Bulk Email Platform with Compliance Check")

        uploaded_file = st.file_uploader("Upload CSV file (columns: email, first_name)", type="csv")

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if 'email' not in df.columns or 'first_name' not in df.columns:
                    st.error("CSV must contain 'email' and 'first_name'.")
                else:
                    email_list = df['email'].tolist()
                    first_name_list = df['first_name'].tolist()

                    subject = st.text_input("Email Subject", "Your Mutual Fund Update")
                    html_file = st.file_uploader("Upload HTML Email Template", type="html")

                    if html_file:
                        html_content = html_file.read().decode("utf-8")
                        st.markdown("**HTML Preview:**")
                        st.markdown(html_content, unsafe_allow_html=True)

                        # Run SEBI Compliance Check
                        sebi_text = fetch_sebi_guidelines()
                        issues = check_compliance(html_content, sebi_text)

                        if issues:
                            st.warning("Compliance Issues Found:")
                            for issue in issues:
                                st.write(f"- {issue}")
                            st.stop()
                        else:
                            st.success("✅ Email passed SEBI compliance check.")

                        # Language Translation
                        language_options = ["en", "hi", "es", "fr", "de", "it", "pt"]
                        selected_language = st.selectbox("Select Email Language", language_options)

                        translated_body = html_content
                        if selected_language != "en":
                            translated_body = asyncio.run(translate_text(html_content, selected_language))
                            st.markdown("**Translated Preview:**")
                            st.markdown(translated_body, unsafe_allow_html=True)

                        if st.checkbox("Preview First Email"):
                            preview_html = translated_body.replace("{first_name}", first_name_list[0])
                            st.markdown(preview_html, unsafe_allow_html=True)

                        if st.checkbox("Confirm and Send"):
                            if st.button("Send Emails Now"):
                                success = 0
                                failure = 0
                                api_key = st.secrets["MAILGUN_API_KEY"]
                                for email, fname in zip(email_list, first_name_list):
                                    body = translated_body.replace("{first_name}", fname)
                                    if send_email(email, subject, body, api_key):
                                        success += 1
                                    else:
                                        failure += 1
                                st.success(f"✅ Sent: {success}")
                                if failure > 0:
                                    st.warning(f"❌ Failed: {failure}")

            except Exception as e:
                st.error(f"CSV Error: {e}")
