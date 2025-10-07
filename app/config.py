import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# LLM token (GitHub model) - expected to be set in env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_MODELS_URL = os.getenv("GITHUB_MODELS_URL", "https://models.github.ai/inference/chat/completions")
GITHUB_API_VERSION = os.getenv("GITHUB_API_VERSION", "2022-11-28")

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")

# Departments mapping
DEPARTMENT_MAP = {
    "Billing Issue": "Accounts",
    "Product Defect": "Product Engineering",
    "Refund Request": "Finance",
    "Technical Issue": "Technical Support",
    "Delivery Problem": "Logistics",
    "Service Quality": "Customer Experience",
    "Others": "General Support",
}

# SLA thresholds in hours
SLA_THRESHOLDS = {
    "Urgent": 12,
    "High": 24,
    "Medium": 72,
    "Low": 168,  # 7 days
}

# Polling interval for IMAP (seconds)
IMAP_POLL_INTERVAL = int(os.getenv("IMAP_POLL_INTERVAL", 300))  # default 5 minutes

# Admin email for alerts
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# Simple API key for admin routes
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "secret_admin_key")

# Database file
# Support DB_PATH env (relative path) to produce SQLAlchemy URL
DB_PATH = os.getenv("DB_PATH", "./complaints.db")
if DB_PATH.startswith("sqlite:///") or DB_PATH.startswith("sqlite://"):
    DATABASE_URL = DB_PATH
else:
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Other settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# LLM model settings
LLM_MODEL = os.getenv("LLM_MODEL", "github/gpt-4o-mini")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 20))
