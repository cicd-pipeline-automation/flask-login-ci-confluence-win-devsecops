import os
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

# ============================================================
# ⚙️ Configuration (environment variables from Jenkins)
# ============================================================
CONFLUENCE_BASE  = os.getenv("CONFLUENCE_BASE")
CONFLUENCE_SPACE = os.getenv("CONFLUENCE_SPACE", "DEMO")
CONFLUENCE_USER  = os.getenv("CONFLUENCE_USER")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")

AUTH = HTTPBasicAuth(CONFLUENCE_USER, CONFLUENCE_TOKEN)
REPORT_DIR = Path("report")

# ============================================================
# 🧩 Helper logic
# ============================================================
def get_version():
    vf = REPORT_DIR / "version.txt"
    return vf.read_text().strip() if vf.exists() else "N/A"


def get_status():
    po = REPORT_DIR / "pytest_output.txt"
    if not po.exists():
        return "UNKNOWN"
    content = po.read_text(encoding="utf-8", errors="ignore").lower()
    return "FAIL" if "failed" in content else "PASS"


def resolve_confluence_link(version, status):
    """Locate latest Confluence child page for current version and status"""
    search_url = f"{CONFLUENCE_BASE}/rest/api/content/search"
    cql = f'title ~ "Test Result Report v{version} ({status})" and space="{CONFLUENCE_SPACE}"'
    r = requests.get(search_url, params={"cql": cql}, auth=AUTH)

    if r.status_code == 200 and r.json().get("results"):
        page = r.json()["results"][0]
        page_id = page["id"]
        title = page["title"]
        link = f"{CONFLUENCE_BASE}/pages/{page_id}/{title.replace(' ', '+')}"
        return link

    # fallback: parent space page
    return f"{CONFLUENCE_BASE}/wiki/spaces/{CONFLUENCE_SPACE}/pages"


if __name__ == "__main__":
    version = get_version()
    status = get_status()
    link = resolve_confluence_link(version, status)
    print(link)
