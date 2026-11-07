import logging

from datetime import datetime

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models.audit import AuditEvent


class AuditLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("mandate_pay.audit")

    def record(self, event: str, order_id: str, metadata: dict | None = None) -> None:
        self._logger.info(
            "payment_audit",
            extra={"audit_event": event, "order_id": order_id},
        )
        if metadata is not None:
            try:
                session: Session = SessionLocal()
                db_event = AuditEvent(
                    order_id=order_id,
                    event_type=event,
                    event_metadata=metadata,
                    created_at=datetime.utcnow(),
                )
                session.add(db_event)
                session.commit()
            except Exception:
                self._logger.error(
                    "audit_persistence_failed",
                    extra={"audit_event": event, "order_id": order_id},
                )
            finally:
                session.close()
        else:
            self._logger.info(
                "audit_skipped_no_metadata",
                extra={"audit_event": event, "order_id": order_id},
            )
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models.audit import AuditEvent


class AuditLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("mandate_pay.audit")

    def record(self, event: str, order_id: str, metadata: dict | None = None) -> None:
        self._logger.info(
            "payment_audit",
            extra={"audit_event": event, "order_id": order_id},
        )
        if metadata is not None:
            try:
                session: Session = SessionLocal()
                db_event = AuditEvent(
                    order_id=order_id,
                    event_type=event,
                    event_metadata=metadata,
                    created_at=datetime.utcnow(),
                )
                session.add(db_event)
                session.commit()
            except Exception:
                self._logger.error(
                    "audit_persistence_failed",
                    extra={"audit_event": event, "order_id": order_id},
                )
            finally:
                session.close()
        else:
            self._logger.info(
                "audit_skipped_no_metadata",
                extra={"audit_event": event, "order_id": order_id},
            )
import logging

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models.audit import AuditEvent


class AuditLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("mandate_pay.audit")

    def record(self, event: str, order_id: str, metadata: dict | None = None) -> None:
        self._logger.info(
            "payment_audit",
            extra={"audit_event": event, "order_id": order_id},
        )
        if metadata is not None:
            try:
                session: Session = SessionLocal()
                db_event = AuditEvent(
                    order_id=order_id,
                    event_type=event,
                    event_metadata=metadata,
                )
                session.add(db_event)
                session.commit()
            except Exception:
                self._logger.error(
                    "audit_persistence_failed",
                    extra={"audit_event": event, "order_id": order_id},
                )
            finally:
                session.close()
        else:
            self._logger.info(
                "audit_skipped_no_metadata",
                extra={"audit_event": event, "order_id": order_id},
            )