import os
import smtplib
import glob
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from bs4 import BeautifulSoup

# ============================================================
# 📦 Configuration
# ============================================================
REPORT_DIR = Path("report")

SMTP_HOST   = os.getenv("SMTP_HOST")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER   = os.getenv("SMTP_USER")
SMTP_PASS   = os.getenv("SMTP_PASS")
REPORT_FROM = os.getenv("REPORT_FROM")
REPORT_TO   = os.getenv("REPORT_TO")

# ============================================================
# 🧩 Helper Functions
# ============================================================
def safe_read(file_path):
    """Safely read a file (UTF-8 fallback)."""
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""

def extract_summary():
    """Extract test and security summary for email body."""
    pytest_output = safe_read(REPORT_DIR / "pytest_output.txt")

    passed = failed = errors = skipped = 0
    if pytest_output:
        import re
        passed = int(re.findall(r"(\d+)\s+passed", pytest_output)[0]) if "passed" in pytest_output else 0
        failed = int(re.findall(r"(\d+)\s+failed", pytest_output)[0]) if "failed" in pytest_output else 0
        errors = int(re.findall(r"(\d+)\s+error", pytest_output)[0]) if "error" in pytest_output else 0
        skipped = int(re.findall(r"(\d+)\s+skipped", pytest_output)[0]) if "skipped" in pytest_output else 0

    total = passed + failed + errors + skipped
    rate = round((passed / total) * 100, 1) if total else 0.0

    bandit_count = safe_read(REPORT_DIR / "bandit_report.html").count("<tr class=\"issue\">")
    dep_vuln_count = safe_read(REPORT_DIR / "dependency_vuln.txt").count("|")
    trivy_high = safe_read(REPORT_DIR / "trivy_report.txt").count("High")
    zap_high = safe_read(REPORT_DIR / "zap_dast_report.html").count("High")

    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "rate": rate,
        "bandit": bandit_count,
        "dep_vuln": dep_vuln_count,
        "trivy_high": trivy_high,
        "zap_high": zap_high
    }

# ============================================================
# 🧠 Build Email Body
# ============================================================
def build_email_body(summary):
    """Generate HTML body for email."""
    color = "#28a745" if summary["failed"] == 0 and summary["errors"] == 0 else "#dc3545"
    status = "PASS ✅" if summary["failed"] == 0 and summary["errors"] == 0 else "FAIL ❌"

    html_body = f"""
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; color: #333; }}
        h2 {{ color: #007bff; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        th {{
            background-color: #f8f9fa;
        }}
      </style>
    </head>
    <body>
      <h2>📊 Jenkins DevSecOps Automated Test & Security Summary</h2>
      <p><b>Status:</b> <span style="color:{color};">{status}</span></p>

      <table>
        <tr><th colspan="2">🧪 Test Summary</th></tr>
        <tr><td>Passed</td><td>{summary["passed"]}</td></tr>
        <tr><td>Failed</td><td>{summary["failed"]}</td></tr>
        <tr><td>Errors</td><td>{summary["errors"]}</td></tr>
        <tr><td>Skipped</td><td>{summary["skipped"]}</td></tr>
        <tr><td>Pass Rate</td><td>{summary["rate"]}%</td></tr>
      </table>

      <table>
        <tr><th colspan="2">🔐 Security Summary</th></tr>
        <tr><td>SAST (Bandit)</td><td>{summary["bandit"]} issues</td></tr>
        <tr><td>Dependency Vulnerabilities</td><td>{summary["dep_vuln"]} issues</td></tr>
        <tr><td>Container Scan (Trivy)</td><td>{summary["trivy_high"]} High</td></tr>
        <tr><td>DAST (OWASP ZAP)</td><td>{summary["zap_high"]} High</td></tr>
      </table>

      <p>🧾 Attached are all the detailed reports for your review:</p>
      <ul>
        <li>✅ test_result_report_v*.html / .pdf</li>
        <li>🔍 bandit_report.html</li>
        <li>🧩 dependency_vuln.txt</li>
        <li>🛡️ trivy_report.txt</li>
        <li>🕵️ zap_dast_report.html</li>
      </ul>

      <p><i>Generated automatically by Jenkins DevSecOps Pipeline</i></p>
    </body>
    </html>
    """
    return html_body

# ============================================================
# ✉️ Send Email
# ============================================================
def send_email():
    summary = extract_summary()
    msg = MIMEMultipart()
    msg["From"] = REPORT_FROM
    msg["To"] = REPORT_TO
    msg["Subject"] = "🔔 Jenkins DevSecOps Test & Security Report"

    msg.attach(MIMEText(build_email_body(summary), "html"))

    # Attach all relevant files
    attachments = [
        "bandit_report.html",
        "dependency_vuln.txt",
        "report.html",
        "test_result_report_v*.html",
        "test_result_report_v*.pdf",
        "trivy_report.txt",
        "version.txt",
        "zap_dast_report.html"
    ]

    attached_count = 0
    for pattern in attachments:
        for file_path in glob.glob(str(REPORT_DIR / pattern)):
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)
                attached_count += 1

    print(f"📎 Attached {attached_count} report files to email.")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ============================================================
# 🚀 Main
# ============================================================
if __name__ == "__main__":
    send_email()
