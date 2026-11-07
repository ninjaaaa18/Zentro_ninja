from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from uuid import uuid4


class OrderNotFound(LookupError):
    """Raised when a transaction order does not exist."""


@dataclass(frozen=True)
class PaymentOrder:
    id: str
    amount: Decimal
    currency: str
    status: str
    created_at: str
    paypal_order_id: str | None = None
    capture_id: str | None = None
    approval_url: str | None = None


class TransactionService:
    def __init__(self) -> None:
        self._orders: dict[str, PaymentOrder] = {}
        self._lock = Lock()

    def create_order(
        self,
        *,
        amount: Decimal,
        currency: str,
        approval_url: str | None = None,
        paypal_order_id: str | None = None,
    ) -> PaymentOrder:
        order = PaymentOrder(
            id=str(uuid4()),
            amount=amount,
            currency=currency,
            status="pending_authorization",
            created_at=datetime.now(timezone.utc).isoformat(),
            approval_url=approval_url,
            paypal_order_id=paypal_order_id,
        )

        with self._lock:
            self._orders[order.id] = order

        return order

    def get_order(self, order_id: str) -> PaymentOrder:
        with self._lock:
            order = self._orders.get(order_id)

        if order is None:
            raise OrderNotFound(order_id)

        return order