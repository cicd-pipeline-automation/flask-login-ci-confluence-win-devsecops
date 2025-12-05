# 🧩 DevSecOps CI/CD Pipeline - Jenkins \| Docker \| Python \| Confluence Integration

This project demonstrates a complete **DevSecOps CI/CD automation**
integrating code scanning, containerization, security validation, and
automated report publishing to **Confluence** with email notifications.

--------------------------------------------------------------------------

## 📦 1. Software Installation Steps

### 🧰 Prerequisites

Ensure you have **Administrator privileges** and internet connectivity.

#### **1. Install Java (for Jenkins)**

``` bash
choco install openjdk11 -y
```

Add to PATH (Windows):

    C:\Program Files\OpenJDK\jdk-11\bin

#### **2. Install Jenkins**

-   Download: <https://www.jenkins.io/download>
-   Run setup as service (default port: 8080)
-   Unlock Jenkins using the admin password found in:\
    `C:\Program Files\Jenkins\secrets\initialAdminPassword`

#### **3. Install Python**

``` bash
choco install python -y
```

Verify:

``` bash
python --version
```

Add PATH:

    C:\Users\<user>\AppData\Local\Programs\Python\Python311\Scripts

#### **4. Install Docker Desktop**

-   Download and install from:
    <https://www.docker.com/products/docker-desktop>
-   Enable WSL2 backend in Docker settings.

#### **5. Install Trivy (Container Security Scanner)**

``` bash
choco install trivy -y
```

Add PATH:

    C:\tools\trivy

#### **6. Verify installations**

``` bash
java -version
jenkins --version
python --version
docker version
trivy --version
```

------------------------------------------------------------------------

## 🏗️ 2. Project Structure

    📁 flask-login-ci-confluence-win-devsecops
     ┣ 📁 app/
     ┣ 📁 report/
     ┣ 📄 Dockerfile
     ┣ 📄 Jenkinsfile
     ┣ 📄 requirements.txt
     ┣ 📄 generate_report.py
     ┣ 📄 publish_report_confluence.py
     ┣ 📄 send_report_email.py
     ┗ 📄 README.md

------------------------------------------------------------------------

## ⚙️ 3. Jenkins CI/CD Pipeline Stages

### 1️⃣ **Setup Encoding**

Ensures Jenkins console uses UTF-8 to prevent Unicode symbol errors.

### 2️⃣ **Checkout GitHub**

Clones the latest repository from GitHub using Jenkins credentials.

### 3️⃣ **Setup Python Environment**

-   Creates a `.venv` virtual environment.
-   Installs dependencies from `requirements.txt`.
-   Caches dependencies to optimize builds.

### 4️⃣ **SAST - Bandit**

Performs static code analysis for Python vulnerabilities and outputs
`bandit_report.html`.

### 5️⃣ **Dependency Vulnerability Scan**

Uses **Safety** to scan outdated or insecure packages → outputs
`dependency_vuln.txt`.

### 6️⃣ **Run Unit Tests (Pytest)**

Executes automated tests, generates HTML test reports and logs results.

### 7️⃣ **Verify Docker Installation**

Ensures Docker is running and accessible to Jenkins.

### 8️⃣ **Build Docker Image**

Builds an application container image from the `Dockerfile`.

### 9️⃣ **Container Security Scan (Trivy)**

Scans the built image for vulnerabilities using Trivy.

### 🔟 **Deploy for DAST Scan (OWASP ZAP)**

Starts the app container for dynamic analysis.

### 11️⃣ **DAST - OWASP ZAP Scan**

Performs runtime security analysis and saves the report
`zap_dast_report.html`.

### 12️⃣ **Generate & Publish Reports**

-   `generate_report.py`: combines test & security summaries into
    HTML/PDF.
-   `publish_report_confluence.py`: uploads results & attachments to
    Confluence.

### 13️⃣ **Send Email Notification**

-   `send_report_email.py`: sends consolidated email with all artifacts
    attached.

------------------------------------------------------------------------

## 🐋 4. Dockerfile Explanation

``` dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /app/
EXPOSE 5000
RUN useradd -m flaskuser
USER flaskuser
ENV FLASK_APP=app.py
CMD ["python", "app.py"]
```

**Explanation:** - Uses a minimal Python base image. - Installs
dependencies securely. - Runs the app as a non-root user for security. -
Exposes port 5000 (Flask default).

------------------------------------------------------------------------

## 🧾 5. requirements.txt Explanation

  Package            Purpose
  ------------------ --------------------------------------------
  `pytest`           Unit testing framework
  `pytest-html`      Generates HTML test reports
  `bandit`           Static Application Security Testing (SAST)
  `safety`           Dependency vulnerability checker
  `fpdf2`            PDF generation for reports
  `beautifulsoup4`   HTML parsing for report extraction
  `requests`         HTTP requests to Confluence API
  `typer`            CLI management utility

------------------------------------------------------------------------

## 🌐 6. Steps to Create a GitHub Repository

``` bash
git init
git remote add origin https://github.com/<username>/<repo>.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

------------------------------------------------------------------------

## 🔑 7. Create GitHub API Token

1.  Go to **GitHub → Settings → Developer settings → Personal access
    tokens → Fine-grained tokens**.
2.  Click **Generate new token**.
3.  Select scopes: `repo`, `workflow`, `admin:repo_hook`.
4.  Copy and save the token securely (used in Jenkins credentials).

------------------------------------------------------------------------

## 📘 8. Create Confluence Space and API Token

1.  Login to your Atlassian account → **Confluence Cloud**.\
2.  Create a space (e.g., `DEMO`).
3.  Create an API token at <https://id.atlassian.com/manage/api-tokens>.
4.  Store this token in Jenkins credentials as `confluence-token`.

------------------------------------------------------------------------

## 📧 9. Create App Email Password (for SMTP)

1.  For Gmail → go to **Account → Security → App passwords**.
2.  Generate app password under "Mail" → "Other (Custom name)".\
3.  Use this 16-character password as `SMTP_PASS`.

------------------------------------------------------------------------

## 🔌 10. Jenkins Plugin Installation

Go to **Manage Jenkins → Plugins → Available Plugins** and install: -
**GitHub Integration Plugin** - **Email Extension Plugin** -
**Confluence Publisher Plugin** - **Pipeline Stage View Plugin** -
**Warnings Next Generation Plugin** - **HTML Publisher Plugin**

Restart Jenkins after installation.

------------------------------------------------------------------------

## 🔐 11. Configure Jenkins Credentials

  ID                     Type               Description
  ---------------------- ------------------ ----------------------
  `smtp-host`            Secret Text        SMTP hostname
  `smtp-user`            Secret Text        SMTP username
  `smtp-pass`            Secret Text        SMTP app password
  `sender-email`         Secret Text        Email sender address
  `receiver-email`       Secret Text        Recipient address
  `confluence-base`      Secret Text        Base Confluence URL
  `confluence-user`      Secret Text        Atlassian email
  `confluence-token`     Secret Text        Atlassian API token
  `github-credentials`   Username & Token   GitHub credentials

------------------------------------------------------------------------

## 🧮 12. Create Jenkins Pipeline Job

1.  Open Jenkins → **New Item → Pipeline**\
2.  Enter Job name: `flask-login-ci-confluence`
3.  Select **Pipeline script from SCM**
    -   SCM: `Git`
    -   Repository URL: `https://github.com/<username>/<repo>.git`
    -   Credentials: `github-credentials`
4.  Script Path: `Jenkinsfile`
5.  Save and click **Build Now**.

------------------------------------------------------------------------

## ✅ Summary

✔️ Automated testing and security scanning.\
✔️ Secure Docker image build and container scanning.\
✔️ Auto-report publishing to Confluence.\
✔️ Automated email with results and artifacts.\
✔️ Full visibility from Jenkins to Confluence and mailbox.

------------------------------------------------------------------------

### 🧠 Author

**DevSecOps Engineer - CI/CD Automation Project**\
Version: `v1.0.0-rc.1`
