import smtplib
from email.mime.text import MIMEText
from .. import config
import logging
from datetime import datetime
from ..database import SessionLocal
from ..models import Complaint

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str):
    if not config.SMTP_USER or not config.SMTP_PASSWORD or not config.SMTP_SERVER:
        logger.warning("SMTP not configured, skipping send_email")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config.SMTP_USER
    msg['To'] = to_email

    try:
        s = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        s.starttls()
        s.login(config.SMTP_USER, config.SMTP_PASSWORD)
        s.sendmail(config.SMTP_USER, [to_email], msg.as_string())
        s.quit()
        return True
    except Exception:
        logger.exception("Failed to send email")
        return False


def send_acknowledgement(complaint_id: int):
    db = SessionLocal()
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        db.close()
        return False
    to_email = c.customer_email
    subj = f"Complaint Received - [Ticket #{c.id}]"
    dept = c.department or "General Support"
    category = c.categories or 'your issue'
    body = (
        f"Dear {c.customer_name or c.customer_email},\n\n"
        f"We've received your complaint (Ticket #{c.id}) regarding {category}.\n"
        f"Our {dept} team will review your case and contact you as soon as possible.\n\n"
        "Regards,\nCustomer Support AI Agent"
    )
    sent = send_email(to_email, subj, body)
    if sent:
        c.acknowledged_at = datetime.utcnow()
        db.add(c)
        db.commit()
    db.close()
    return sent


def alert_admin(subject: str, message: str):
    if config.ADMIN_EMAIL:
        return send_email(config.ADMIN_EMAIL, subject, message)
    else:
        logger.warning("Admin alert: %s - %s", subject, message)
        return False
