from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from .database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True, index=True)
    channel = Column(String(50), nullable=False, default="Web")
    subject = Column(String(512), nullable=True)
    description = Column(Text, nullable=False)
    keywords = Column(String(512), nullable=True)
    sentiment = Column(String(50), nullable=True)
    severity = Column(String(50), nullable=True)
    categories = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="New")
    received_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    sla_violation = Column(Boolean, default=False)
    llm_classification = Column(Text, nullable=True)
    llm_routing = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
