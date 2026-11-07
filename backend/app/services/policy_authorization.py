from typing import Protocol


class PolicyEngineUnavailable(RuntimeError):
    """Raised when the Mandate Pay policy engine cannot verify authorization."""


class PolicyAuthorizationVerifier(Protocol):
    def verify_authorization(
        self,
        *,
        order_id: str,
        authorization_id: str,
    ) -> bool:
        """Independently verify the authorization with the backend policy engine."""


class UnconfiguredPolicyEngineVerifier:
    def verify_authorization(
        self,
        *,
        order_id: str,
        authorization_id: str,
    ) -> bool:
        raise PolicyEngineUnavailable(
            "The Mandate Pay policy engine integration is not configured."
        )
