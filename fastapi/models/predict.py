from enum import Enum

from pydantic import BaseModel, Field

from models.base import StrictBaseModel


class Intent(str, Enum):
    """As 5 classes de `Ticket Type` do dataset (alvo da classificação)."""

    TECHNICAL_ISSUE = "Technical issue"
    BILLING_INQUIRY = "Billing inquiry"
    PRODUCT_INQUIRY = "Product inquiry"
    REFUND_REQUEST = "Refund request"
    CANCELLATION_REQUEST = "Cancellation request"


class PredictRequest(StrictBaseModel):
    """Corpo de POST /predict. Herda de StrictBaseModel (extra='forbid'):
    campos além de ticket_subject/ticket_description resultam em 422."""

    ticket_subject: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Assunto do ticket (equivale à coluna `Ticket Subject`).",
        examples=["Product setup"],
    )
    ticket_description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Texto livre do cliente (equivale à coluna `Ticket Description`).",
        examples=["I can't connect my device to the Wi-Fi network."],
    )


class PredictResponse(BaseModel):
    """Resposta de POST /predict e GET /predictions/{prediction_id}.

    Estado atual (placeholder): ainda NÃO há modelo de classificação
    integrado. A API devolve sempre `intent="Technical issue"` com
    `confidence=0.0`. O valor 0.0 é proposital — sinaliza ao cliente que a
    intenção retornada é fixa e não deve ser usada para nenhuma decisão.
    """

    id: str = Field(
        ...,
        description=(
            "Identificador (UUID4) da predição no histórico do usuário "
            "autenticado; consultável em GET /predictions/{prediction_id}."
        ),
    )
    intent: Intent = Field(
        ...,
        description=(
            "Intenção prevista, uma das 5 classes de `Ticket Type`. "
            "Placeholder: hoje é sempre 'Technical issue'."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Probabilidade estimada pelo modelo para a classe em `intent`, "
            "no intervalo [0, 1] (ex.: saída softmax/predict_proba). Com "
            "5 classes balanceadas, ~0.2 equivale a um palpite aleatório. "
            "Placeholder: hoje é sempre 0.0, indicando que NÃO houve "
            "inferência real e que `intent` não deve ser considerada."
        ),
    )
