import os
import re
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ============================================================
# 🔧 Environment Configuration
# ============================================================
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
TO_EMAIL = os.getenv("REPORT_TO")
FROM_EMAIL = os.getenv("REPORT_FROM")

REPORT_DIR = "report"
VERSION_FILE = os.path.join(REPORT_DIR, "version.txt")
BASE_NAME = "test_result_report"

# Reports
PYTEST_LOG = os.path.join(REPORT_DIR, "pytest_output.txt")
BANDIT_REPORT = os.path.join(REPORT_DIR, "bandit_report.html")
SAFETY_REPORT = os.path.join(REPORT_DIR, "dependency_vuln.txt")
TRIVY_REPORT = os.path.join(REPORT_DIR, "trivy_report.html")
ZAP_REPORT = os.path.join(REPORT_DIR, "zap_dast_report.html")


# ============================================================
# 🧩 Helper Functions
# ============================================================
def read_version():
    """Return latest report version number."""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            return int(f.read().strip())
    return 1


def safe_read(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def extract_test_status():
    """Detect PASS / FAIL from pytest_output.txt."""
    text = safe_read(PYTEST_LOG)
    passed = failed = errors = skipped = 0
    if m := re.search(r"(\d+)\s+passed", text, re.I): passed = int(m.group(1))
    if m := re.search(r"(\d+)\s+failed", text, re.I): failed = int(m.group(1))
    if m := re.search(r"(\d+)\s+errors?", text, re.I): errors = int(m.group(1))
    if m := re.search(r"(\d+)\s+skipped", text, re.I): skipped = int(m.group(1))

    total = passed + failed + errors + skipped
    rate = (passed / total * 100) if total else 0
    status = "PASS" if failed == 0 and errors == 0 else "FAIL"
    emoji = "✅" if status == "PASS" else "❌"
    summary = f"{emoji} {passed} passed, ❌ {failed} failed, ⚠️ {errors} errors, ⏭ {skipped} skipped — Pass rate: {rate:.1f}%"
    return status, summary, rate


def extract_security_summary():
    """Summarize findings from DevSecOps scans."""
    bandit_html = safe_read(BANDIT_REPORT)
    safety_txt = safe_read(SAFETY_REPORT)
    trivy_html = safe_read(TRIVY_REPORT)
    zap_html = safe_read(ZAP_REPORT)

    bandit_issues = len(re.findall(r"<tr class=\"issue\">", bandit_html)) if bandit_html else "N/A"
    safety_vulns = len(re.findall(r"\|", safety_txt)) if safety_txt else "N/A"

    if trivy_html:
        critical = len(re.findall(r"Critical", trivy_html, re.I))
        high = len(re.findall(r"High", trivy_html, re.I))
        trivy_summary = f"{critical} Critical / {high} High"
    else:
        trivy_summary = "N/A"

    if zap_html:
        high = len(re.findall(r"High", zap_html))
        medium = len(re.findall(r"Medium", zap_html))
        zap_summary = f"{high} High / {medium} Medium"
    else:
        zap_summary = "N/A"

    # Determine risk level
    risk_score = 0
    for val in (bandit_issues, safety_vulns):
        if isinstance(val, int):
            risk_score += val
    if isinstance(trivy_summary, str) and "Critical" in trivy_summary:
        crit_count = int(re.findall(r"(\d+)", trivy_summary.split("Critical")[0])[0]) if "Critical" in trivy_summary else 0
        risk_score += crit_count
    if isinstance(zap_summary, str) and "High" in zap_summary:
        try:
            zap_high = int(re.findall(r"(\d+)", zap_summary.split("High")[0])[0])
            risk_score += zap_high
        except Exception:
            pass

    if risk_score == 0:
        risk_level = "🟢 Low"
    elif risk_score < 5:
        risk_level = "🟠 Medium"
    else:
        risk_level = "🔴 High"

    return {
        "SAST_Bandit": bandit_issues,
        "Dependency_Safety": safety_vulns,
        "Container_Trivy": trivy_summary,
        "DAST_ZAP": zap_summary,
        "Risk_Level": risk_level,
    }


# ============================================================
# 📧 Email Sender
# ============================================================
def send_email():
    version = read_version()
    pdf_path = os.path.join(REPORT_DIR, f"{BASE_NAME}_v{version}.pdf")
    if not os.path.exists(pdf_path):
        raise SystemExit(f"❌ PDF report not found: {pdf_path}")

    status, summary, rate = extract_test_status()
    sec_summary = extract_security_summary()
    emoji = "✅" if status == "PASS" else "❌"
    color = "green" if status == "PASS" else "red"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build email
    msg = EmailMessage()
    msg["Subject"] = f"{emoji} DevSecOps Pipeline {status} (v{version}) - {sec_summary['Risk_Level']} Risk"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    # Plain text version
    msg.set_content(f"""
DevSecOps Pipeline Report (v{version})
--------------------------------------
Status: {status}
Summary: {summary}

Security Overview:
- SAST (Bandit): {sec_summary['SAST_Bandit']}
- Dependency (Safety): {sec_summary['Dependency_Safety']}
- Container (Trivy): {sec_summary['Container_Trivy']}
- DAST (ZAP): {sec_summary['DAST_ZAP']}
- Risk Level: {sec_summary['Risk_Level']}

Generated: {timestamp}
PDF attached.
""")

    # HTML version
    msg.add_alternative(f"""
    <html>
    <body style="font-family:Arial,sans-serif; color:#222;">
        <h2>{emoji} DevSecOps Pipeline 
            <span style="color:{color}; font-weight:bold;">{status}</span> (v{version})</h2>

        <p><b>Summary:</b> {summary}</p>

        <h3>🔐 Security Scan Overview</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
            <tr style="background-color:#f2f2f2; text-align:center;">
                <th>Scan Type</th><th>Findings</th>
            </tr>
            <tr><td>SAST (Bandit)</td><td align="center">{sec_summary['SAST_Bandit']}</td></tr>
            <tr><td>Dependency (Safety)</td><td align="center">{sec_summary['Dependency_Safety']}</td></tr>
            <tr><td>Container (Trivy)</td><td align="center">{sec_summary['Container_Trivy']}</td></tr>
            <tr><td>DAST (OWASP ZAP)</td><td align="center">{sec_summary['DAST_ZAP']}</td></tr>
            <tr style="background-color:#e6f7ff;">
                <td><b>Overall Risk Level</b></td>
                <td align="center"><b>{sec_summary['Risk_Level']}</b></td>
            </tr>
        </table>

        <p style="margin-top:15px;">📄 The full PDF report is attached.</p>
        <p style="font-size:0.9em; color:#777;">
           Generated automatically on {timestamp}.
        </p>
    </body></html>
    """, subtype="html")

    # Attach PDF report
    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(pdf_path))

    # Send email
    print(f"📤 Sending DevSecOps report email to {TO_EMAIL}...")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo()
            if SMTP_PORT == 587:
                s.starttls()
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print(f"✅ Email sent successfully ({status}, {sec_summary['Risk_Level']}).")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# ============================================================
# 🚀 Entry Point
# ============================================================
if __name__ == "__main__":
    try:
        send_email()
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
