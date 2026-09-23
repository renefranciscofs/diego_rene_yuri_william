from enum import Enum

from pydantic import BaseModel, Field

from models.base import StrictBaseModel


class Intent(str, Enum):
    TECHNICAL_ISSUE = "Technical issue"
    BILLING_INQUIRY = "Billing inquiry"
    PRODUCT_INQUIRY = "Product inquiry"
    REFUND_REQUEST = "Refund request"
    CANCELLATION_REQUEST = "Cancellation request"


class PredictRequest(StrictBaseModel):
    """Corpo de POST /predict. Herda de StrictBaseModel (extra='forbid'):
    campos além de ticket_subject/ticket_description resultam em 422."""

    ticket_subject: str = Field(..., min_length=1, max_length=200)
    ticket_description: str = Field(..., min_length=1, max_length=5000)


class PredictResponse(BaseModel):
    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
