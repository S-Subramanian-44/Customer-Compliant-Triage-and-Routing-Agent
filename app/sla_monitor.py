import threading
import time
import logging
from datetime import datetime, timedelta
from .database import SessionLocal
from .models import Complaint
from .config import SLA_THRESHOLDS
from .utils.notifier import alert_admin
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


def check_sla_once():
    db = SessionLocal()
    now = datetime.utcnow()
    try:
        complaints = db.query(Complaint).filter(Complaint.status != 'Resolved').all()
    except OperationalError as e:
        logger.error("Database schema error during SLA check: %s", e)
        db.close()
        return 0
    violations = []
    for c in complaints:
        severity = c.severity or 'Medium'
        hours = SLA_THRESHOLDS.get(severity, 72)
        due = c.created_at + timedelta(hours=hours) if c.created_at else None
        if due and now > due and not c.sla_violation:
            c.sla_violation = True
            db.add(c)
            violations.append(c)
    db.commit()
    db.close()

    for v in violations:
        subj = f"SLA Violation for Ticket #{v.id}"
        msg = f"Ticket {v.id} assigned to {v.department} is overdue. Severity={v.severity}.\nSubject: {v.subject}\nReceived: {v.received_at}\nCreated: {v.created_at}"
        alert_admin(subj, msg)
        logger.warning("SLA violation detected: %s", v.id)

    return len(violations)


def start_sla_loop(stop_event, interval_seconds=300):
    while not stop_event.is_set():
        try:
            n = check_sla_once()
            logger.info("SLA check completed, violations=%s", n)
        except Exception:
            logger.exception("Error in SLA loop")
        time.sleep(interval_seconds)
