import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
import asyncio
from fpdf import FPDF
import tempfile
import os

# Config
MAILGUN_DOMAIN = "evertechcms.in"
MAILGUN_FROM = "Ever CMS <mailgun@evertechcms.in>"

# Validate API Key
def check_api_key(user_key):
    valid_keys = [
        st.secrets["api_keys"].get("key_1"),
        st.secrets["api_keys"].get("key_2"),
        st.secrets["api_keys"].get("key_3"),
        st.secrets["api_keys"].get("key_4"),
        st.secrets["api_keys"].get("key_5")
    ]
    return user_key in valid_keys

# Fetch SEBI guidelines (summary used internally for matching)
def get_sebi_rules():
    return {
        "Forecasts": "Avoid forecasting NAV or returns unless backed by reserves or guarantees.",
        "Guarantees": "Do not guarantee returns unless supported by third-party or reserves.",
        "Comparisons": "Avoid unwarranted comparisons or superlatives.",
        "Partial Returns": "Show performance only with standardized methods across 1, 3, 5 years.",
        "Risk Disclosure": "Must include risk factors and avoid hedging risk statements.",
        "Unsubstantiated Claims": "Do not make claims on management skills without 3-year track record."
    }

# Compliance engine
def perform_compliance_check(content):
    rules = get_sebi_rules()
    issues = []
    passed = True

    checks = {
        "Forecasts": ["forecast", "projected return", "expected nav", "predicted"],
        "Guarantees": ["guaranteed return", "no risk", "assured income"],
        "Comparisons": ["best fund", "top performing", "number one", "ranked first"],
        "Partial Returns": ["up by", "grew by", "% growth", "since inception"],
        "Risk Disclosure": ["low risk", "safe", "capital guaranteed"],
        "Unsubstantiated Claims": ["award-winning", "superior strategy", "exclusive insights"]
    }

    content_lower = content.lower()

    for rule, phrases in checks.items():
        for phrase in phrases:
            if phrase in content_lower:
                passed = False
                issues.append(f"Violation of '{rule}': Found phrase '{phrase}' — {rules[rule]}")
                break

    return passed, issues

# Create PDF compliance report
def generate_pdf_report(passed, issues, original_html):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    title = "SEBI Compliance Report"
    pdf.cell(200, 10, txt=title, ln=True, align='C')

    pdf.ln(10)
    pdf.set_font("Arial", size=11)

    pdf.cell(200, 10, txt=f"Compliance Status: {'PASS' if passed else 'FAIL'}", ln=True)

    pdf.ln(5)
    pdf.multi_cell(0, 10, "Reasons:" if issues else "No issues found.")

    for issue in issues:
        pdf.multi_cell(0, 10, f"- {issue}")

    pdf.ln(10)
    pdf.multi_cell(0, 10, "Extract from uploaded HTML content (first 500 characters):")
    pdf.set_font("Courier", size=9)
    pdf.multi_cell(0, 10, original_html[:500] + "..." if len(original_html) > 500 else original_html)

    tmp_path = os.path.join(tempfile.gettempdir(), "compliance_report.pdf")
    pdf.output(tmp_path)
    return tmp_path

# Email sender
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
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# Translation (optional)
async def translate_text(text, target_language):
    translator = Translator()
    try:
        translated = await translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return text

# UI
st.set_page_config(layout="centered")
st.title("📧 AI Email Campaign with SEBI Compliance Check")

user_key = st.text_input("🔐 Enter your API key:", type="password")

if user_key:
    if not check_api_key(user_key):
        st.error("❌ Invalid API key.")
        st.stop()

    uploaded_file = st.file_uploader("📥 Upload CSV (columns: email, first_name)", type="csv")
    html_file = st.file_uploader("🖋️ Upload HTML Email Template", type="html")

    if uploaded_file and html_file:
        try:
            df = pd.read_csv(uploaded_file)
            if "email" not in df.columns or "first_name" not in df.columns:
                st.error("CSV must have columns: email, first_name")
                st.stop()

            html_content = html_file.read().decode("utf-8")
            st.markdown("### 🔍 HTML Preview")
            st.markdown(html_content, unsafe_allow_html=True)

            # Compliance Check
            passed, issues = perform_compliance_check(html_content)
            report_path = generate_pdf_report(passed, issues, html_content)

            st.markdown("### 📄 Compliance Report")
            with open(report_path, "rb") as f:
                st.download_button("⬇️ Download Report", f, file_name="compliance_report.pdf")

            if passed:
                st.success("✅ HTML is SEBI compliant.")
            else:
                st.error("❌ Compliance violations found. Please fix before proceeding.")
                st.stop()

            # Translation
            language_options = ["en", "hi", "fr", "de", "es"]
            lang = st.selectbox("🌐 Translate email to:", language_options)

            if lang != "en":
                html_content = asyncio.run(translate_text(html_content, lang))
                st.markdown("### 🌐 Translated Preview")
                st.markdown(html_content, unsafe_allow_html=True)

            if st.checkbox("📤 Preview First Email"):
                st.markdown(html_content.replace("{first_name}", df['first_name'][0]), unsafe_allow_html=True)

            if st.checkbox("📨 Confirm & Send"):
                if st.button("🚀 Send Campaign"):
                    api_key = st.secrets["MAILGUN_API_KEY"]
                    success, failure = 0, 0
                    for email, fname in zip(df['email'], df['first_name']):
                        content = html_content.replace("{first_name}", fname)
                        if send_email(email, subject="SEBI-Compliant Newsletter", html_content=content, api_key=api_key):
                            success += 1
                        else:
                            failure += 1
                    st.success(f"✅ Sent: {success} emails")
                    if failure:
                        st.warning(f"❌ Failed: {failure} emails")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
