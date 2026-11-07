import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class PaymentProviderNotConfigured(RuntimeError):
    """Raised when a PayPal operation is requested before integration is configured."""



class PayPalCredentialsNotConfigured(RuntimeError):
    """Raised when usable PayPal credentials are not available."""



class PayPalAuthenticationFailed(RuntimeError):
    """Raised when PayPal Sandbox authentication fails."""



class PayPalOrderCreationFailed(RuntimeError):
    """Raised when PayPal order creation fails."""



class PayPalCaptureFailed(RuntimeError):
    """Raised when PayPal capture fails."""



class PayPalClient:
    timeout_seconds = 10.0

    def get_access_token(self) -> str:
        client_id = os.getenv("PAYPAL_CLIENT_ID", "").strip()
        client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
        base_url = os.getenv(
            "PAYPAL_BASE_URL",
            "https://api-m.sandbox.paypal.com",
        ).strip().rstrip("/")

        if (
            not client_id
            or not client_secret
            or client_id.startswith("replace_with_your_")
            or client_secret.startswith("replace_with_your_")
        ):
            raise PayPalCredentialsNotConfigured

        try:
            response = httpx.post(
                f"{base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PayPalAuthenticationFailed from exc

        if not isinstance(payload, dict):
            raise PayPalAuthenticationFailed
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise PayPalAuthenticationFailed
        return access_token

    def create_order(self, *, amount: str, currency: str) -> dict:
        """Create a PayPal Sandbox order and return order ID and approval URL.

        Returns dict with keys: order_id, approval_url
        """
        access_token = self.get_access_token()
        base_url = os.getenv(
            "PAYPAL_BASE_URL",
            "https://api-m.sandbox.paypal.com",
        ).strip().rstrip("/")

        try:
            response = httpx.post(
                f"{base_url}/v2/checkout/orders",
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [
                        {
                            "amount": {"currency_code": currency.upper(), "value": str(amount)},
                        }
                    ],
                },
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except httpx.HTTPError as exc:
            raise PayPalOrderCreationFailed from exc

        if not isinstance(payload, dict):
            raise PayPalOrderCreationFailed

        order_id = payload.get("id")
        if not isinstance(order_id, str) or not order_id:
            raise PayPalOrderCreationFailed

        # Extract approval URL from links
        approval_url = None
        links = payload.get("links") or []
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break

        return {"order_id": order_id, "approval_url": approval_url}

    def capture_order(self, order_id: str) -> dict:
        """Capture a PayPal Sandbox order and return capture ID and status.

        Uses the correct PayPal Orders v2 endpoint:
        POST /v2/checkout/orders/{order_id}/capture

        Raises PayPalCredentialsNotConfigured if no token available.
        Raises PayPalAuthenticationFailed if auth fails.
        Raises PayPalCaptureFailed if capture fails.
        """
        access_token = self.get_access_token()
        base_url = os.getenv(
            "PAYPAL_BASE_URL",
            "https://api-m.sandbox.paypal.com",
        ).strip().rstrip("/")

        try:
            response = httpx.post(
                f"{base_url}/v2/checkout/orders/{order_id}/capture",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
            # 201 = captured, 200 = already captured
            if response.status_code not in (200, 201):
                raise PayPalCaptureFailed

            payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PayPalCaptureFailed from exc

        if not isinstance(payload, dict):
            raise PayPalCaptureFailed

        capture_id = payload.get("id")
        status = payload.get("status")
        # Also capture the order status from the response
        order_status = payload.get("status")

        return {"capture_id": capture_id, "status": status, "order_status": order_status}
