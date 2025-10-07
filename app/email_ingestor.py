import imaplib
import email
from email.header import decode_header
import time
import logging
from datetime import datetime
from .config import IMAP_SERVER, IMAP_USER, IMAP_PASSWORD, IMAP_POLL_INTERVAL
from .database import SessionLocal
from .models import Complaint
from .utils.extract_metadata import extract_text_from_email
from .utils.notifier import send_acknowledgement
from .utils.router import process_and_route

logger = logging.getLogger(__name__)


def poll_inbox_once():
    if not IMAP_SERVER or not IMAP_USER or not IMAP_PASSWORD:
        logger.warning("IMAP credentials not configured")
        return 0

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASSWORD)
        mail.select('inbox')
        status, messages = mail.search(None, '(UNSEEN)')
        if status != 'OK':
            return 0
        msgs = messages[0].split()
        count = 0
        for num in msgs:
            res, msg_data = mail.fetch(num, '(RFC822)')
            if res != 'OK':
                continue
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    from_ = msg.get('From')
                    # Try to parse the From header into name and email
                    from_name = None
                    from_email = None
                    try:
                        parsed = email.utils.parseaddr(from_)
                        from_name = parsed[0] if parsed and parsed[0] else None
                        from_email = parsed[1] if parsed and parsed[1] else from_
                    except Exception:
                        from_email = from_
                    subject = msg.get('Subject')
                    date = msg.get('Date')
                    try:
                        body = extract_text_from_email(msg)
                    except Exception:
                        body = ""

                    # Create complaint record
                    db = SessionLocal()
                    complaint = Complaint(
                        customer_name=from_name,
                        customer_email=from_email,
                        channel='Email',
                        subject=subject,
                        description=body,
                        received_at=datetime.utcnow()
                    )
                    db.add(complaint)
                    db.commit()
                    db.refresh(complaint)
                    db.close()

                    # Process routing/classification asynchronously (simple call)
                    process_and_route(complaint.id)

                    # Send acknowledgement
                    send_acknowledgement(complaint.id)

                    count += 1
            # mark as seen
            mail.store(num, '+FLAGS', '\\Seen')
        mail.logout()
        return count
    except Exception:
        logger.exception("Failed to poll IMAP inbox")
        return 0


def start_polling_loop(stop_event):
    while not stop_event.is_set():
        try:
            new = poll_inbox_once()
            logger.info("IMAP polled, new messages=%s", new)
        except Exception:
            logger.exception("Error in IMAP poll loop")
        time.sleep(IMAP_POLL_INTERVAL)
