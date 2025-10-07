# AI Complaint Triage & Routing Agent

This project implements an autonomous backend to ingest, classify, prioritize, route, and manage customer complaints using an LLM and SQLite.

Setup

1. Create a virtualenv and install dependencies:

   python -m venv .venv
   .venv\Scripts\activate
   pip install -r app/requirements.txt

2. Create a `.env` file with the following variables:

GITHUB_TOKEN=your_github_token_here
GITHUB_MODELS_URL=https://api.github.com/your/models/path  # optional, default targets GitHub Models endpoint
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=yourpassword
IMAP_SERVER=imap.gmail.com
IMAP_USER=you@example.com
IMAP_PASSWORD=yourpassword
ADMIN_EMAIL=admin@example.com
ADMIN_API_KEY=supersecret

3. Run the app:

   uvicorn app.main:app --reload

API Endpoints

- POST /submit_complaint
- GET /get_complaints
- GET /get_summary
- PATCH /update_status/{id}
- POST /trigger_ingest

- Notes

- LLM integration prefers the GitHub Models API when `GITHUB_TOKEN` is set. You can optionally override the models URL with `GITHUB_MODELS_URL`.
- If you don't have a GitHub token, you can set an OpenAI-style key in `LLM_API_KEY` or `OPENAI_API_KEY` and `LLM_API_URL`.
- IMAP polling will start automatically if IMAP_SERVER is set.
- This is a minimal implementation; extend as needed for production use.
