import os
import re
import base64
from io import BytesIO
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

# ----------------------------
# File Paths
# ----------------------------
REPORT_DIR = 'report'
INPUT_REPORT = os.path.join(REPORT_DIR, 'report.html')
VERSION_FILE = os.path.join(REPORT_DIR, 'version.txt')
BASE_NAME = 'test_result_report'

# DevSecOps reports
BANDIT_REPORT = os.path.join(REPORT_DIR, 'bandit_report.html')
SAFETY_REPORT = os.path.join(REPORT_DIR, 'dependency_vuln.txt')
TRIVY_REPORT = os.path.join(REPORT_DIR, 'trivy_report.html')
ZAP_REPORT = os.path.join(REPORT_DIR, 'zap_dast_report.html')


# ----------------------------
# Extract Summary Counts
# ----------------------------
def extract_summary_counts(html_text):
    matches = {
        'passed': re.search(r'(\d+)\s+Passed', html_text),
        'failed': re.search(r'(\d+)\s+Failed', html_text),
        'skipped': re.search(r'(\d+)\s+Skipped', html_text),
        'error': re.search(r'(\d+)\s+Errors?', html_text),
    }
    return {k: int(v.group(1)) if v else 0 for k, v in matches.items()}


# ----------------------------
# Version Helper
# ----------------------------
def get_next_report_filename():
    os.makedirs(REPORT_DIR, exist_ok=True)
    pattern = re.compile(rf"{re.escape(BASE_NAME)}_v(\d+)\.html$")
    existing = [f for f in os.listdir(REPORT_DIR) if pattern.match(f)]
    next_version = max([int(pattern.match(f).group(1)) for f in existing], default=0) + 1
    return os.path.join(REPORT_DIR, f"{BASE_NAME}_v{next_version}.html"), next_version


# ----------------------------
# Chart Creator
# ----------------------------
def create_summary_chart(counts):
    labels = ['Passed', 'Failed', 'Skipped', 'Error']
    values = [counts['passed'], counts['failed'], counts['skipped'], counts['error']]
    colors_ = ['#4CAF50', '#F44336', '#FF9800', '#9E9E9E']

    fig, ax = plt.subplots(figsize=(6, 2))
    bars = ax.barh(labels, values, color=colors_)
    ax.set_xlabel('Number of Tests')
    ax.set_title('Test Summary Overview')
    ax.bar_label(bars, labels=[str(v) for v in values], label_type='edge')
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf


# ----------------------------
# Helper - Extract Security Results
# ----------------------------
def extract_security_findings():
    results = {}

    # Bandit (SAST)
    if os.path.exists(BANDIT_REPORT):
        with open(BANDIT_REPORT, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            findings = len(re.findall(r'<tr class="issue">', text))
            results['SAST_Bandit'] = findings
    else:
        results['SAST_Bandit'] = 'N/A'

    # Safety (Dependencies)
    if os.path.exists(SAFETY_REPORT):
        with open(SAFETY_REPORT, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            vuln_count = len(re.findall(r'\|', content))
            results['Dependency_Safety'] = vuln_count
    else:
        results['Dependency_Safety'] = 'N/A'

    # Trivy (Container)
    if os.path.exists(TRIVY_REPORT):
        with open(TRIVY_REPORT, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
            critical = len(re.findall(r'Critical', html, re.IGNORECASE))
            high = len(re.findall(r'High', html, re.IGNORECASE))
            results['Container_Trivy'] = f"{critical} Critical / {high} High"
    else:
        results['Container_Trivy'] = 'N/A'

    # ZAP (DAST)
    if os.path.exists(ZAP_REPORT):
        with open(ZAP_REPORT, 'r', encoding='utf-8', errors='ignore') as f:
            zap_html = f.read()
            high = len(re.findall(r'High', zap_html))
            medium = len(re.findall(r'Medium', zap_html))
            results['DAST_ZAP'] = f"{high} High / {medium} Medium"
    else:
        results['DAST_ZAP'] = 'N/A'

    return results


# ----------------------------
# PDF Report Generator
# ----------------------------
def generate_pdf_report(version, counts, pass_rate, chart_buf, sec_findings):
    pdf_filename = os.path.join(REPORT_DIR, f"{BASE_NAME}_v{version}.pdf")
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>DevSecOps Test & Security Report - v{version}</b>", styles['Title']))
    elements.append(Spacer(1, 12))

    # Test Summary
    summary = f"""
    <b>Passed:</b> <font color='green'>{counts['passed']}</font> |
    <b>Failed:</b> <font color='red'>{counts['failed']}</font> |
    <b>Skipped:</b> <font color='orange'>{counts['skipped']}</font> |
    <b>Errors:</b> <font color='gray'>{counts['error']}</font><br/>
    <b>Pass Rate:</b> {pass_rate:.1f}%
    """
    elements.append(Paragraph(summary, styles['Normal']))
    elements.append(Spacer(1, 20))

    img = Image(chart_buf)
    img._restrictSize(400, 150)
    elements.append(img)
    elements.append(Spacer(1, 20))

    # Security Summary Table
    data = [["Scan Type", "Findings"],
            ["SAST (Bandit)", sec_findings["SAST_Bandit"]],
            ["Dependency (Safety)", sec_findings["Dependency_Safety"]],
            ["Container (Trivy)", sec_findings["Container_Trivy"]],
            ["DAST (ZAP)", sec_findings["DAST_ZAP"]]]

    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(Paragraph("<b>Security Scan Summary</b>", styles['Heading2']))
    elements.append(table)

    doc.build(elements)
    print(f"📄 PDF report generated: {pdf_filename}")


# ----------------------------
# HTML Enhancer
# ----------------------------
def enhance_html_report():
    if not os.path.exists(INPUT_REPORT):
        raise SystemExit(f"❌ Base report not found: {INPUT_REPORT}")

    with open(INPUT_REPORT, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    html_text = str(soup)
    counts = extract_summary_counts(html_text)
    total = sum(counts.values()) or 1
    pass_rate = (counts['passed'] / total) * 100

    sec_findings = extract_security_findings()
    chart_buf = create_summary_chart(counts)

    # Inject DevSecOps Summary
    sec_html = f"""
    <div style="background-color:#eef7ff; border:1px solid #007bff; padding:15px; margin:15px 0;">
      <h2>🔐 DevSecOps Security Summary</h2>
      <ul>
        <li><b>SAST (Bandit):</b> {sec_findings['SAST_Bandit']} findings</li>
