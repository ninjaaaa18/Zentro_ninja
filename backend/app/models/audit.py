import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    event_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"AuditEvent(order_id={self.order_id}, event_type={self.event_type})"
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    event_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"AuditEvent(order_id={self.order_id}, event_type={self.event_type})"