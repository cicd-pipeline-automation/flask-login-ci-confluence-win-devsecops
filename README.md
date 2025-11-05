# 🔐 DevSecOps CI/CD Pipeline --- Flask Test Automation & Security Reporting

A complete **DevSecOps-driven Jenkins CI/CD pipeline** integrating: -
Automated testing (Pytest + HTML/PDF reports) - Static code analysis
(Bandit) - Dependency scanning (Safety) - Container security scanning
(Trivy) - Dynamic application testing (OWASP ZAP) - Secure email
notifications - Report publishing to **Atlassian Confluence**

------------------------------------------------------------------------

## 🧩 1. Prerequisites & Software Installation

### ☕ 1.1 Install Java

Jenkins requires Java (JDK 17 or newer):

``` bash
java -version
```

Set the `JAVA_HOME` environment variable:

``` powershell
setx JAVA_HOME "C:\Program Files\Java\jdk-17"
setx PATH "%PATH%;%JAVA_HOME%\bin"
```

### 🐍 1.2 Install Python 3

Download and install Python ≥3.10 from
[python.org](https://www.python.org/downloads/). ✅ Ensure **"Add Python
to PATH"** is selected during installation.

Verify:

``` bash
python --version
pip --version
```

### ⚙️ 1.3 Install Jenkins LTS

Download and install the latest **Jenkins LTS** for Windows or Linux:\
👉 <https://www.jenkins.io/download/>

Start Jenkins and open:

``` bash
http://localhost:8080
```

Unlock Jenkins using:

    C:\ProgramData\Jenkins\.jenkins\secrets\initialAdminPassword

------------------------------------------------------------------------

## ⚙️ 2. Jenkins UI & Plugin Setup

Install these plugins from **Manage Jenkins → Manage Plugins**:

  Category             Plugin
  -------------------- ---------------------------------
  Source Control       GitHub Plugin
  Build Management     Pipeline Plugin
  Email Notification   Email Extension Plugin
  Python               ShiningPanda / Python Plugin
  Reporting            HTML Publisher Plugin
  Security             Warnings Next Generation Plugin
  Documentation        Confluence Publisher Plugin

Restart Jenkins after installation.

------------------------------------------------------------------------

## 🔑 3. Jenkins Credentials Configuration

  ----------------------------------------------------------------------------------------------------
  ID                     Description                         Example
  ---------------------- ----------------------------------- -----------------------------------------
  `github-credentials`   GitHub PAT or username/token        `<username> / ghp_xxxxxxxxxx`

  `smtp-host`            SMTP Server                         `smtp.gmail.com`

  `smtp-user`            Sender Email                        `noreply@yourdomain.com`

  `smtp-pass`            App Password                        `abcd1234xyz`

  `confluence-user`      Atlassian User                      `admin@yourdomain.com`

  `confluence-token`     API Token                           `ATAT-xxxxxx-xxxxxx`

  `confluence-base`      Base URL                            `https://yourdomain.atlassian.net/wiki`
  ----------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 🧪 4. Repository Structure

    .
    ├── app.py
    ├── test_app.py
    ├── templates/
    │   ├── login.html
    │   └── dashboard.html
    ├── report/
    ├── requirements.txt
    ├── generate_report.py
    ├── send_report_email.py
    ├── publish_report_confluence.py
    └── Jenkinsfile

------------------------------------------------------------------------

## ⚙️ 5. Jenkins Pipeline Overview

  Stage                            Description
  -------------------------------- -----------------------------------
  **Checkout GitHub**              Clone repository
  **Setup Python**                 Create virtual environment
  **Install Dependencies**         Install all required libraries
  **Run Tests (Pytest)**           Execute automated tests
  **Run Bandit (SAST)**            Static analysis on source code
  **Run Safety (Dependencies)**    Check vulnerable dependencies
  **Run Trivy (Container Scan)**   Scan Docker image
  **Run OWASP ZAP (DAST)**         Perform dynamic scan
  **Generate Report**              Combine all results into HTML/PDF
  **Send Email**                   Notify results to stakeholders
  **Publish to Confluence**        Upload HTML/PDF and summary page

------------------------------------------------------------------------

## 🧾 Example Jenkinsfile Snippet

``` groovy
pipeline {
  agent any
  options { timestamps() }

  environment {
    SMTP_HOST = credentials('smtp-host')
    SMTP_USER = credentials('smtp-user')
    SMTP_PASS = credentials('smtp-pass')
    REPORT_FROM = credentials('sender-email')
    REPORT_TO = credentials('receiver-email')
    CONFLUENCE_BASE = credentials('confluence-base')
    CONFLUENCE_USER = credentials('confluence-user')
    CONFLUENCE_TOKEN = credentials('confluence-token')
    CONFLUENCE_SPACE = 'DEMO'
  }

  stages {
    stage('Checkout') {
      steps {
        git credentialsId: 'github-credentials', url: 'https://github.com/devopsuser/flask-devsecops-pipeline.git'
      }
    }

    stage('Setup & Install') {
      steps {
        bat '''
          python -m venv .venv
          .venv\Scripts\pip install --upgrade pip
          .venv\Scripts\pip install -r requirements.txt
        '''
      }
    }

    stage('Run Tests') {
      steps {
        bat '.venv\Scripts\pytest --html=report/report.html --self-contained-html || exit 0'
      }
    }

    stage('Security Scans') {
      steps {
        bat '''
          .venv\Scripts\bandit -r app.py -f html -o report/bandit_report.html || exit 0
          .venv\Scripts\safety check --full-report > report/dependency_vuln.txt || exit 0
        '''
      }
    }

    stage('Generate Reports & Publish') {
      steps {
        bat '''
          .venv\Scripts\python generate_report.py
          .venv\Scripts\python send_report_email.py
          .venv\Scripts\python publish_report_confluence.py
        '''
      }
    }
  }

  post {
    success {
      echo '✅ Pipeline completed successfully.'
    }
    failure {
      echo '❌ Pipeline failed. Check Jenkins logs and Confluence report.'
    }
  }
}
```

------------------------------------------------------------------------

## 🧱 6. DevSecOps Toolchain Summary

  Category                  Tool                     Purpose
  ------------------------- ------------------------ -------------------------------
  SCM                       GitHub                   Source control
  CI/CD                     Jenkins                  Pipeline orchestration
  App Framework             Flask                    Sample web app
  Testing                   Pytest + pytest-html     Automated testing
  Reporting                 ReportLab + Matplotlib   Enhanced visual reports
  Static Security (SAST)    Bandit                   Code analysis
  Dependency Scanning       Safety                   Library vulnerability checks
  Container Scanning        Trivy                    Image vulnerability detection
  Dynamic Security (DAST)   OWASP ZAP                Runtime vulnerability testing
  Notifications             SMTP                     Email alerts
  Documentation             Confluence               Publish reports and summaries

------------------------------------------------------------------------

## 🔄 7. CI/CD Workflow Summary

1.  Developer pushes code to GitHub.\
2.  Jenkins automatically triggers via webhook.\
3.  Code is tested, analyzed, and scanned.\
4.  Reports are generated (HTML + PDF).\
5.  Email with summary + attachments is sent.\
6.  Confluence is updated with results and risk status.

✅ Final Outcome: **Unified build, test, and security visibility** for
your DevSecOps workflow.

------------------------------------------------------------------------

## 📜 Maintainer Info

**Maintainer:** Your Name\
**Team / Department:** DevSecOps Engineering\
**Organization:** Your Company\
**Contact:** you@company.com

------------------------------------------------------------------------
