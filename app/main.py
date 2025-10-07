import uvicorn
import logging
from fastapi import FastAPI
from .database import init_db
from .routes import complaints, admin
from .sla_monitor import start_sla_loop
from .email_ingestor import start_polling_loop
import threading
import os
from .logging_config import setup_logging

logger = setup_logging(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')) if os.getenv('LOG_LEVEL', 'INFO').isalpha() else logging.INFO)

app = FastAPI(title="AI Complaint Triage & Routing Agent")

app.include_router(complaints.router)
app.include_router(admin.router)

# init DB
init_db()

# background threads
stop_event = threading.Event()

# Start SLA monitor thread
sla_thread = threading.Thread(target=start_sla_loop, args=(stop_event, 300), daemon=True)
sla_thread.start()

# Start IMAP poller if configured
if os.getenv('IMAP_SERVER'):
    imap_thread = threading.Thread(target=start_polling_loop, args=(stop_event,), daemon=True)
    imap_thread.start()

@app.on_event("shutdown")
def shutdown_event():
    stop_event.set()

if __name__ == '__main__':
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
