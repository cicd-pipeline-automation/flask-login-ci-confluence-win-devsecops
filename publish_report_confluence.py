import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from pathlib import Path

# ============================================================
# ⚙️ Configuration
# ============================================================
CONFLUENCE_BASE  = os.getenv("CONFLUENCE_BASE")
CONFLUENCE_USER  = os.getenv("CONFLUENCE_USER")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE", "DEMO")
CONFLUENCE_PARENT_TITLE = os.getenv("CONFLUENCE_TITLE", "DevSecOps Test Result Report")

REPORT_DIR = Path("report")
AUTH = HTTPBasicAuth(CONFLUENCE_USER, CONFLUENCE_TOKEN)
HEADERS = {"Content-Type": "application/json"}


# ============================================================
# 🔍 Helper Functions
# ============================================================
def safe_read(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def get_page_id(title, space):
    """Return page ID if it exists."""
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    params = {"spaceKey": space, "title": title}
    r = requests.get(url, params=params, auth=AUTH)
    if r.status_code == 200 and r.json().get("results"):
        return r.json()["results"][0]["id"]
    return None


def create_page(title, body, space, parent_id=None):
    """Create a new Confluence page."""
    url = f"{CONFLUENCE_BASE}/rest/api/content/"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]
    r = requests.post(url, json=payload, auth=AUTH, headers=HEADERS)
    if r.status_code in (200, 201):
        page_id = r.json()["id"]
        print(f"✅ Created page: {title} (ID: {page_id})")
        return page_id
    else:
        print(f"❌ Failed to create page '{title}': {r.status_code} - {r.text}")
        return None


def update_page(page_id, title, body, version):
    """Update an existing Confluence page."""
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}"
    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": version + 1},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    r = requests.put(url, json=payload, auth=AUTH, headers=HEADERS)
    if r.status_code in (200, 201):
        print(f"✅ Updated page '{title}' to version {version + 1}")
    else:
        print(f"❌ Failed to update page '{title}': {r.status_code} - {r.text}")


# ============================================================
# 📎 Attachment Upload (Fixed for Atlassian Cloud)
# ============================================================
def upload_attachment(page_id, file_path):
    """Attach or replace files on a Confluence page (visible under attachments)."""
    file_name = os.path.basename(file_path)
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/child/attachment"
    headers = {"X-Atlassian-Token": "no-check"}  # Required for Cloud uploads

    # Upload new file
    with open(file_path, "rb") as f:
        files = {"file": (file_name, f, "application/octet-stream")}
        r = requests.post(url, files=files, auth=AUTH, headers=headers)

    if r.status_code in (200, 201):
        print(f"📎 Successfully uploaded: {file_name}")
        return

    # Handle duplicate (same filename)
    if "same file name" in r.text or r.status_code in (400, 409):
        attach_url = f"{url}?filename={file_name}"
        get_resp = requests.get(attach_url, auth=AUTH)
        if get_resp.status_code == 200 and get_resp.json().get("results"):
            attach_id = get_resp.json()["results"][0]["id"]
            update_url = f"{CONFLUENCE_BASE}/rest/api/content/{attach_id}/data"
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                update_resp = requests.post(update_url, files=files, auth=AUTH, headers=headers)
                if update_resp.status_code in (200, 201):
                    print(f"↻ Updated existing attachment: {file_name}")
                else:
                    print(f"⚠️ Failed to update attachment {file_name}: {update_resp.status_code}")
    else:
        print(f"❌ Failed to upload {file_name}: {r.status_code} - {r.text}")


# ============================================================
# 🧠 Page Content Builders
# ============================================================
def build_child_page_body(version):
    """Child page body that lists attachments inline."""
    return f"""
    <h2>DevSecOps Test & Security Report v{version}</h2>
    <p><b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p>This page contains all test & security reports generated from Jenkins.</p>
    <p><i>All related artifacts are attached below.</i></p>
    <p><ac:structured-macro ac:name="attachments"></ac:structured-macro></p>
    """


def build_parent_page_body():
    """Rebuild the parent page with links to all report versions."""
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    params = {"spaceKey": CONFLUENCE_SPACE, "limit": 200}
    r = requests.get(url, params=params, auth=AUTH)
    links = ""
    if r.status_code == 200:
        for page in r.json().get("results", []):
            title = page["title"]
            if title.startswith("Test Result Report v"):
                page_id = page["id"]
                links += f'<li><a href="{CONFLUENCE_BASE}/pages/{page_id}/{title.replace(" ", "+")}">{title}</a></li>'
    body = f"""
    <h1>DevSecOps Test & Security Reports</h1>
    <p>This page is automatically updated by Jenkins with links to all versioned reports.</p>
    <ul>{links}</ul>
    <p><i>Generated automatically by the Jenkins DevSecOps Pipeline.</i></p>
    """
    return body


# ============================================================
# 🚀 Main Logic
# ============================================================
if __name__ == "__main__":
    version = "N/A"
    vf = REPORT_DIR / "version.txt"
    if vf.exists():
        version = vf.read_text().strip()

    # Detect PASS/FAIL status from pytest output
    pytest_output = safe_read(REPORT_DIR / "pytest_output.txt").lower()
    status = "PASS" if "failed" not in pytest_output else "FAIL"

    # Ensure parent page exists
    parent_id = get_page_id(CONFLUENCE_PARENT_TITLE, CONFLUENCE_SPACE)
    if not parent_id:
        parent_id = create_page(CONFLUENCE_PARENT_TITLE, "<p>Index page for DevSecOps reports.</p>", CONFLUENCE_SPACE)

    # Create new child page
    child_title = f"Test Result Report v{version} ({status})"
    child_body = build_child_page_body(version)
    child_id = create_page(child_title, child_body, CONFLUENCE_SPACE, parent_id)

    # Upload artifacts
    if child_id:
        print("📤 Uploading report artifacts...")
        for file in REPORT_DIR.glob("*"):
            if file.is_file():
                upload_attachment(child_id, str(file))

    # Update parent index
    if parent_id:
        body = build_parent_page_body()
        update_page(parent_id, CONFLUENCE_PARENT_TITLE, body, version=1)
        print("✅ Parent index page updated successfully.")
