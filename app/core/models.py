from pydantic import BaseModel, Field, HttpUrl
from typing import Literal


class Provider(BaseModel):
    name: str
    base_url: HttpUrl
    api_key: str
    priority: int = 1
    fallback_allowed: bool = True


class ServiceItem(BaseModel):
    service_id: int
    name: str
    platform: str
    rate: float
    min_qty: int
    max_qty: int


class CreateOrderRequest(BaseModel):
    user_id: int
    platform: str
    service_id: int
    quantity: int = Field(gt=0)
    link: HttpUrl
    link: str


class CreateOrderResponse(BaseModel):
    order_id: str
    provider: str
    status: Literal["created", "queued", "failed"]
    charged_amount: float
    currency: Literal["INR"] = "INR"


class CashfreeWebhookPayload(BaseModel):
    order_id: str | None = None
    order_amount: float = 0
    order_status: str | None = None
    customer_details: dict = Field(default_factory=dict)
