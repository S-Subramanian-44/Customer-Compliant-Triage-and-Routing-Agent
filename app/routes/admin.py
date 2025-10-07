from fastapi import APIRouter, Header, HTTPException
from ..database import SessionLocal
from ..models import Complaint
from ..config import ADMIN_API_KEY
from ..utils.serializers import complaint_to_dict

router = APIRouter()


def check_api_key(x_api_key: str = Header(None)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/admin/complaints")
def list_all_complaints(x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    db = SessionLocal()
    items = db.query(Complaint).all()
    resp = [complaint_to_dict(c) for c in items]
    db.close()
    return resp

@router.post("/admin/alert/{id}")
def manual_alert(id: int, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    from ..utils.notifier import alert_admin
    db = SessionLocal()
    c = db.query(Complaint).filter(Complaint.id == id).first()
    db.close()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    subj = f"Manual alert for ticket #{c.id}"
    msg = f"Ticket details:\n{c.subject}\n{c.description}"
    alert_admin(subj, msg)
    return {"alerted": True}


@router.get("/admin/complaint/{id}")
def get_complaint_detail(id: int, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    db = SessionLocal()
    c = db.query(Complaint).filter(Complaint.id == id).first()
    db.close()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    return complaint_to_dict(c)
