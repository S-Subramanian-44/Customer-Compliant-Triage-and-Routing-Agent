import json
from datetime import datetime


def _iso(dt: datetime):
    return dt.isoformat() if dt else None


def complaint_to_dict(c):
    # Build a clean, structured dict from a Complaint ORM instance
    try:
        categories = [s.strip() for s in (c.categories or '').split(',') if s.strip()]
    except Exception:
        categories = []
    try:
        keywords = [s.strip() for s in (c.keywords or '').split(',') if s.strip()]
    except Exception:
        keywords = []

    # Try to parse LLM JSON blobs if they are JSON strings
    def _maybe_json(val):
        if not val:
            return None
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return val

    return {
        "id": c.id,
        "customer_name": c.customer_name,
        "customer_email": c.customer_email,
        "channel": c.channel,
        "subject": c.subject,
        "description": c.description,
        "keywords": keywords,
        "sentiment": c.sentiment,
        "severity": c.severity,
        "categories": categories,
        "department": c.department,
        "status": c.status,
        "llm_classification": _maybe_json(c.llm_classification),
        "llm_routing": _maybe_json(c.llm_routing),
        "received_at": _iso(c.received_at),
        "acknowledged_at": _iso(c.acknowledged_at),
        "resolved_at": _iso(c.resolved_at),
        "created_at": _iso(getattr(c, 'created_at', None)),
        "updated_at": _iso(getattr(c, 'updated_at', None)),
        "sla_violation": bool(c.sla_violation),
    }
