import logging
import json
from ..llm_utils import classify_complaint, severity_and_routing
from ..sentiment_analyzer import analyze_sentiment
from .keywords import extract_keywords
from ..database import SessionLocal
from ..models import Complaint
from ..config import DEPARTMENT_MAP

logger = logging.getLogger(__name__)


def process_and_route(complaint_id: int):
    db = SessionLocal()
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        db.close()
        return

    # classify
    cls = classify_complaint(c.description)
    categories = cls.get('categories') if isinstance(cls, dict) else []
    confidence = cls.get('confidence', 0) if isinstance(cls, dict) else 0
    # store raw llm classification JSON when available
    llm_class_raw = None
    try:
        llm_class_raw = json.dumps(cls) if not isinstance(cls, str) else str(cls)
    except Exception:
        llm_class_raw = str(cls)
    if not categories:
        categories = ["Others"]

    # sentiment
    sentiment = analyze_sentiment(c.description)

    # extract keywords (LLM-based extractor preferred)
    keywords = extract_keywords(c.description)

    # severity and routing (pass sentiment and keywords for better fallback)
    sr = severity_and_routing(c.description, categories, sentiment=sentiment, keywords=keywords)
    severity = sr.get('severity') if isinstance(sr, dict) else 'Medium'
    department = sr.get('routed_department') if isinstance(sr, dict) else DEPARTMENT_MAP.get(categories[0], 'General Support')

    c.categories = ",".join(categories)
    c.sentiment = sentiment
    c.severity = severity
    c.department = department
    c.keywords = ','.join(keywords) if keywords else None
    c.llm_classification = llm_class_raw
    # store llm routing raw if provided
    try:
        llm_routing_raw = json.dumps(sr) if isinstance(sr, dict) else str(sr)
    except Exception:
        llm_routing_raw = str(sr)
    c.llm_routing = llm_routing_raw

    db.add(c)
    db.commit()

    # Capture values before closing the session to avoid DetachedInstanceError
    result = {
        'id': c.id,
        'categories': categories,
        'confidence': confidence,
        'sentiment': sentiment,
        'severity': severity,
        'department': department,
    }
    # Log using captured values
    logger.info("Processed complaint %s, categories=%s, severity=%s, dept=%s", result['id'], result['categories'], result['severity'], result['department'])

    db.close()

    return result
