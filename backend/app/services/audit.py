import logging
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.audit import AuditEvent


class AuditLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("mandate_pay.audit")

    def record(self, event: str, order_id: str, metadata: Optional[dict] = None) -> None:
        self._logger.info(
            "payment_audit",
            extra={"audit_event": event, "order_id": order_id},
        )
        session: Session = SessionLocal()
        try:
            db_event = AuditEvent(
                id=str(uuid.uuid4()),
                order_id=order_id,
                event_type=event,
                event_metadata=metadata or {},
            )
            session.add(db_event)
            session.commit()
        except Exception:
            self._logger.error(
                "audit_persistence_failed",
                extra={"audit_event": event, "order_id": order_id},
            )
            session.rollback()
        finally:
            session.close()