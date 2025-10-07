from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from ..database import SessionLocal, init_db
from ..models import Complaint
from ..utils.serializers import complaint_to_dict
from ..utils.router import process_and_route
from ..utils.notifier import send_acknowledgement
from datetime import datetime

router = APIRouter()

class SubmitComplaint(BaseModel):
    customer_name: Optional[str]
    customer_email: Optional[str]
    complaint_description: str
    subject: Optional[str] = None
    channel: Optional[str] = "Web"

@router.post("/submit_complaint")
def submit_complaint(payload: SubmitComplaint):
    db = SessionLocal()
    c = Complaint(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        channel=payload.channel,
        subject=payload.subject,
        description=payload.complaint_description,
        received_at=datetime.utcnow()
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    # Process classification/routing
    result = process_and_route(c.id)

    # Send acknowledgement
    send_acknowledgement(c.id)

    resp = {"id": c.id, "processed": result, "complaint": complaint_to_dict(c)}
    db.close()
    return resp

@router.get("/get_complaints")
def get_complaints(status: Optional[str] = None, severity: Optional[str] = None, department: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None):
    db = SessionLocal()
    q = db.query(Complaint)
    if status:
        q = q.filter(Complaint.status == status)
    if severity:
        q = q.filter(Complaint.severity == severity)
    if department:
        q = q.filter(Complaint.department == department)
    if date_from:
        q = q.filter(Complaint.created_at >= date_from)
    if date_to:
        q = q.filter(Complaint.created_at <= date_to)
    items = q.all()
    resp = [complaint_to_dict(c) for c in items]
    db.close()
    return resp

@router.get("/get_summary")
def get_summary():
    db = SessionLocal()
    total = db.query(Complaint).count()
    by_category = {}
    by_severity = {}
    sla_violations = db.query(Complaint).filter(Complaint.sla_violation == True).count()
    complaints = db.query(Complaint).all()
    for c in complaints:
        cats = (c.categories or 'Others').split(',')
        for cat in cats:
            by_category[cat] = by_category.get(cat, 0) + 1
        sev = c.severity or 'Medium'
        by_severity[sev] = by_severity.get(sev, 0) + 1
    db.close()
    return {"total": total, "by_category": by_category, "by_severity": by_severity, "sla_violations": sla_violations}

@router.patch("/update_status/{id}")
def update_status(id: int, status: str):
    db = SessionLocal()
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        db.close()
        raise HTTPException(status_code=404, detail="Not found")
    c.status = status
    if status == 'Resolved':
        c.resolved_at = datetime.utcnow()
    db.add(c)
    db.commit()
    db.close()
    return {"id": id, "status": status}

@router.post("/trigger_ingest")
def trigger_ingest():
    # Manual trigger - call IMAP poll once
    from ..email_ingestor import poll_inbox_once
    n = poll_inbox_once()
    return {"new_messages": n}
