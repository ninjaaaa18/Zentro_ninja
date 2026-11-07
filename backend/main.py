from fastapi import FastAPI

from app.api.routes.payments import router as payments_router
from app.services.audit import AuditLogger
from app.services.paypal import PayPalClient
from app.services.policy_authorization import (
    PolicyAuthorizationVerifier,
    UnconfiguredPolicyEngineVerifier,
)
from app.services.transactions import TransactionService


def create_app(
    *,
    policy_verifier: PolicyAuthorizationVerifier | None = None,
    paypal_client: PayPalClient | None = None,
    transaction_service: TransactionService | None = None,
    audit_logger: AuditLogger | None = None,
) -> FastAPI:
    application = FastAPI(
        title="Mandate Pay API",
        description="Payment authorization and transaction audit API.",
        version="0.1.0",
    )
    application.state.policy_verifier = (
        policy_verifier or UnconfiguredPolicyEngineVerifier()
    )
    application.state.paypal_client = paypal_client or PayPalClient()
    application.state.transaction_service = transaction_service or TransactionService()
    application.state.audit_logger = audit_logger or AuditLogger()
    
    # Initialize audit database tables
    from app.database import create_tables
    create_tables()

    @application.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(payments_router, prefix="/payments", tags=["payments"])
    return application


app = create_app()
