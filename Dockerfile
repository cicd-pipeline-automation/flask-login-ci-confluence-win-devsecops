# ================================================
# 🐋 Secure Flask Application - Root-level Dockerfile
# ================================================
FROM python:3.11-slim AS base

# Set working directory inside container
WORKDIR /app

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install essential tools (curl used in HEALTHCHECK)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt from root
COPY requirements.txt .

# Install dependencies securely
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire Flask app folder into container
COPY app/ /app/

# Expose Flask default port
EXPOSE 5000

# Create non-root user for better security
RUN useradd -m flaskuser
USER flaskuser

# Default Flask environment
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False

# Healthcheck for CI/CD
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:5000/health || exit 1

# Run Flask app
CMD ["python", "app.py"]
