import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import base64

# Function to check API key
def check_api_key(user_key):
    valid_keys = [
        st.secrets["api_keys"].get("key_1"),
        st.secrets["api_keys"].get("key_2"),
        st.secrets["api_keys"].get("key_3"),
        st.secrets["api_keys"].get("key_4"),
        st.secrets["api_keys"].get("key_5")
    ]
    return user_key in valid_keys

# Function to scrape SEBI regulations
def scrape_sebi_regulations(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        regulations = soup.get_text(separator="\n").strip()
        return regulations
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching SEBI regulations: {e}")
        return None

# Function to analyze compliance
def analyze_compliance(html_content, regulations):
    soup = BeautifulSoup(html_content, 'html.parser')
    email_text = soup.get_text(separator=" ").strip()
    
    non_compliance_issues = []
    regulation_lines = regulations.split("\n")
    
    for line in regulation_lines:
        if line.strip() and line.lower() in email_text.lower():
            non_compliance_issues.append(line.strip())
    
    return non_compliance_issues

# Function to generate a compliance report
def generate_compliance_report(html_content, regulations, non_compliance_issues):
    report = "### Compliance Report\n\n"
    report += "**Regulations Checked:**\n"
    report += regulations + "\n\n"
    
    report += "**Compliance Issues Found:**\n"
    if non_compliance_issues:
        for issue in non_compliance_issues:
            report += f"- {issue}\n"
    else:
        report += "No compliance issues found.\n\n"
    
    report += "**Analyzed Email Content:**\n"
    report += html_content
    return report

# Function to download compliance report
def download_report(report_text):
    b64 = base64.b64encode(report_text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="compliance_report.txt">Download Compliance Report</a>'
    st.markdown(href, unsafe_allow_html=True)

# Streamlit app
SEBI_URL = "https://www.sebi.gov.in/sebi_data/commondocs/cirmf42000_h.html"
user_key = st.text_input("Enter your API key to access the app:", type="password")

if user_key:
    if not check_api_key(user_key):
        st.error("Invalid API Key! Access Denied.")
    else:
        st.title("AI Powered Newsletter & Email Compliance Checker")

        # Scrape SEBI Regulations
        st.markdown("### Fetching SEBI Regulations")
        regulations = scrape_sebi_regulations(SEBI_URL)

        if regulations:
            st.success("SEBI Regulations Fetched Successfully")

            # Upload CSV
            uploaded_file = st.file_uploader("Upload CSV file (columns: email, first_name)", type="csv")

            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    if 'email' not in df.columns or 'first_name' not in df.columns:
                        st.error("CSV must contain 'email' and 'first_name' columns.")
                    else:
                        email_list = df['email'].tolist()
                        first_name_list = df['first_name'].tolist()

                        subject = st.text_input("Email Subject", "Your Newsletter")

                        # HTML Template Upload
                        html_file = st.file_uploader("Upload HTML Email Template", type="html")
                        html_content = ""
                        if html_file is not None:
                            try:
                                html_content = html_file.read().decode("utf-8")
                                st.markdown("### Uploaded HTML Template Preview")
                                st.markdown(html_content, unsafe_allow_html=True)

                                # Analyze Compliance
                                st.markdown("### Compliance Analysis")
                                non_compliance_issues = analyze_compliance(html_content, regulations)

                                if non_compliance_issues:
                                    st.error("Compliance Issues Found:")
                                    for issue in non_compliance_issues:
                                        st.markdown(f"- {issue}")
                                else:
                                    st.success("No compliance issues found! You may proceed.")

                                # Generate and Download Compliance Report
                                report = generate_compliance_report(html_content, regulations, non_compliance_issues)
                                download_report(report)

                                # Proceed Option
                                proceed = st.checkbox("I have reviewed the compliance report and wish to proceed.")
                                if proceed:
                                    st.success("You are ready to send your email campaign!")

                            except Exception as e:
                                st.error(f"Error reading HTML file: {e}")
                except Exception as e:
                    st.error(f"Error processing CSV: {e}")
