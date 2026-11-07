from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class CaptureOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorization_id: str = Field(min_length=1, max_length=255)

    @field_validator("authorization_id")
    @classmethod
    def authorization_id_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("authorization_id must not be blank")
        return value


class PaymentOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    amount: Decimal
    currency: str
    status: str
    created_at: str
    paypal_order_id: str | None = None
    approval_url: str | None = None
    paypal_order_id: str | None = None
    approval_url: str | None = None
