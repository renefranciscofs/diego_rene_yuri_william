from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    TECHNICAL_ISSUE = "Technical issue"
    BILLING_INQUIRY = "Billing inquiry"
    PRODUCT_INQUIRY = "Product inquiry"
    REFUND_REQUEST = "Refund request"
    CANCELLATION_REQUEST = "Cancellation request"


class PredictRequest(BaseModel):
    ticket_subject: str = Field(..., min_length=1, max_length=200)
    ticket_description: str = Field(..., min_length=1, max_length=5000)


class PredictResponse(BaseModel):
    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
