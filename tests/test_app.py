import pytest
from app import app
import os

@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-key"
    )
    with app.test_client() as client:
        yield client


# ================================
# 🧩 Functional Tests
# ================================
def test_login_page_shows(client):
    """✅ Login page should render correctly."""
    rv = client.get("/login")
    assert rv.status_code == 200
    assert b"Login" in rv.data


def test_login_success(client):
    """✅ Valid login should redirect to dashboard."""
    rv = client.post(
        "/login",
        data={"username": "alice", "password": "password123"},
        follow_redirects=True
    )
    assert rv.status_code == 200
    assert b"Welcome" in rv.data or b"Dashboard" in rv.data


def test_login_failure(client):
    """✅ Invalid login should show an error message."""
    rv = client.post(
        "/login",
        data={"username": "alice", "password": "wrongpass"},
        follow_redirects=True
    )
    assert rv.status_code == 200
    assert b"Invalid username or password" in rv.data


def test_logout_redirects_to_login(client):
    """✅ Logout should clear session and redirect."""
    client.post("/login", data={"username": "alice", "password": "password123"})
    rv = client.get("/logout", follow_redirects=True)
    assert rv.status_code == 200
    assert b"Login" in rv.data


def test_dashboard_requires_auth(client):
    """✅ Dashboard access requires login."""
    rv = client.get("/dashboard", follow_redirects=True)
    assert rv.status_code == 200
    assert b"Login" in rv.data or b"Please log in" in rv.data


# ================================
# 🔒 Security & Header Validation
# ================================
def test_security_headers(client):
    """✅ Response should include secure HTTP headers."""
    rv = client.get("/login")
    headers = rv.headers
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"].lower() == "nosniff"
    assert "Content-Security-Policy" in headers


# ================================
# 🩺 Health Check for DevSecOps
# ================================
def test_health_check(client):
    """✅ Health endpoint should respond with OK."""
    rv = client.get("/health")
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data["status"] == "ok"
    assert "flask-login-demo" in json_data["app"]


# ================================
# ⚠️ Intentional Fail Trigger
# ================================
def test_force_failure_for_notification():
    """
    ❌ Intentional failure for Jenkins/Confluence test result validation.
    Set FORCE_FAIL=false to skip.
    """
    force_fail = os.getenv("FORCE_FAIL", "true").lower() == "true"
    if force_fail:
        pytest.fail("Intentional failure for CI/CD notification test")
    else:
        assert True
