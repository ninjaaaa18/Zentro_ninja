from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import (
    CaptureOrderRequest,
    CreateOrderRequest,
    PaymentOrderResponse,
)
from app.services.audit import AuditLogger
from app.database import SessionLocal
from app.services.paypal import (
    PayPalAuthenticationFailed,
    PayPalClient,
    PayPalCredentialsNotConfigured,
    PaymentProviderNotConfigured,
    PayPalOrderCreationFailed,
    PayPalCaptureFailed,
)
from app.services.policy_authorization import (
    PolicyAuthorizationVerifier,
    PolicyEngineUnavailable,
)
from app.services.transactions import OrderNotFound, TransactionService

router = APIRouter()


@router.get("/paypal/connection-test")
def paypal_connection_test(request: Request) -> dict[str, str]:
    paypal: PayPalClient = request.app.state.paypal_client

    try:
        paypal.get_access_token()
    except PayPalCredentialsNotConfigured as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal Sandbox credentials are not configured.",
        ) from error
    except PayPalAuthenticationFailed as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal Sandbox connection test failed.",
        ) from error

    return {
        "status": "ok",
        "message": "PayPal Sandbox connection successful.",
    }


def _services(
    request: Request,
) -> tuple[TransactionService, PolicyAuthorizationVerifier, PayPalClient, AuditLogger]:
    return (
        request.app.state.transaction_service,
        request.app.state.policy_verifier,
        request.app.state.paypal_client,
        request.app.state.audit_logger,
    )


@router.post(
    "/create-order",
    response_model=PaymentOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    payload: CreateOrderRequest,
    request: Request,
) -> PaymentOrderResponse:
    transactions, _, paypal, audit = _services(request)

    try:
        paypal_order = paypal.create_order(
            amount=str(payload.amount),
            currency=payload.currency,
        )
    except PayPalCredentialsNotConfigured as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal Sandbox credentials are not configured.",
        ) from error
    except PayPalOrderCreationFailed as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal order creation failed.",
        ) from error

    order = transactions.create_order(
        amount=payload.amount,
        currency=payload.currency,
        approval_url=paypal_order.get("approval_url"),
        paypal_order_id=paypal_order["order_id"],
    )

    audit.record("order_created", order.id)
    audit.record("paypal_order_created", order.id)

    return PaymentOrderResponse.model_validate({
        "id": order.id,
        "amount": order.amount,
        "currency": order.currency,
        "status": order.status,
        "created_at": order.created_at,
        "paypal_order_id": order.paypal_order_id,
        "approval_url": order.approval_url,
    })


@router.post(
    "/capture/{order_id}",
    response_model=PaymentOrderResponse,
)
def capture_order(
    order_id: str,
    payload: CaptureOrderRequest,
    request: Request,
) -> PaymentOrderResponse:
    transactions, policy_verifier, paypal, audit = _services(request)

    try:
        order = transactions.get_order(order_id)
    except OrderNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found.",
        ) from error

    try:
        authorized = policy_verifier.verify_authorization(
            order_id=order_id,
            authorization_id=payload.authorization_id,
        )
    except PolicyEngineUnavailable as error:
        audit.record("policy_verification_unavailable", order_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mandate Pay policy authorization service is unavailable.",
        ) from error

    if not authorized:
        audit.record("policy_authorization_rejected", order_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid Mandate Pay policy authorization is required.",
        )

    audit.record("policy_authorization_verified", order_id)

    if order.capture_id:
        audit.record("capture_already_completed", order_id)
        return PaymentOrderResponse.model_validate({
            "id": order.id,
            "amount": order.amount,
            "currency": order.currency,
            "status": "captured",
            "created_at": order.created_at,
            "paypal_order_id": order.paypal_order_id,
            "capture_id": order.capture_id,
            "approval_url": order.approval_url,
        })

    audit.record("capture_requested", order_id)

    try:
        capture = paypal.capture_order(order.paypal_order_id or order_id)
    except PayPalCredentialsNotConfigured as error:
        audit.record("capture_not_configured", order_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal Sandbox credentials are not configured.",
        ) from error
    except PayPalAuthenticationFailed as error:
        audit.record("capture_auth_failed", order_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal capture authentication failed.",
        ) from error
    except PayPalCaptureFailed as error:
        audit.record("capture_failed", order_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PayPal capture failed.",
        ) from error
    except PaymentProviderNotConfigured as error:
        audit.record("capture_not_configured", order_id)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PayPal capture integration is not configured.",
        ) from error

    capture_id = capture.get("capture_id")
    capture_status = capture.get("status")
    order_status = capture.get("order_status", capture_status or "captured")

    updated_order = type(order)(
        id=order.id,
        amount=order.amount,
        currency=order.currency,
        status=order_status or "captured",
        created_at=order.created_at,
        paypal_order_id=order.paypal_order_id,
        capture_id=capture_id,
        approval_url=order.approval_url,
    )

    with transactions._lock:
        transactions._orders[order.id] = updated_order

    audit.record("capture_successful", order_id)

    return PaymentOrderResponse.model_validate({
        "id": updated_order.id,
        "amount": updated_order.amount,
        "currency": updated_order.currency,
        "status": updated_order.status,
        "created_at": updated_order.created_at,
        "paypal_order_id": updated_order.paypal_order_id,
        "capture_id": updated_order.capture_id,
        "approval_url": updated_order.approval_url,
    })
@router.get("/{order_id}/audit", response_model=dict)
def get_audit_trail(order_id: str, request: Request) -> dict:
    audit_logger = request.app.state.audit_logger
    session = SessionLocal()
    try:
        from app.models.audit import AuditEvent
        events = (
            session.query(AuditEvent)
            .filter(AuditEvent.order_id == order_id)
            .order_by(AuditEvent.created_at.asc())
            .all()
        )
        event_list = [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "event_metadata": event.event_metadata,
            }
            for event in events
        ]
        return {"order_id": order_id, "audit_events": event_list}
    except Exception:
        return {"order_id": order_id, "audit_events": []}
    finally:
        session.close()


@router.get(
    "/{order_id}",
    response_model=PaymentOrderResponse,
)
def get_order(
    order_id: str,
    request: Request,
) -> PaymentOrderResponse:
    transactions, _, _, _ = _services(request)

    try:
        order = transactions.get_order(order_id)
    except OrderNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found.",
        ) from error

    return PaymentOrderResponse.model_validate(order)