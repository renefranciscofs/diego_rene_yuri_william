from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from models.predict import Intent, PredictRequest, PredictResponse
from models.user import User
from security.oauth2 import get_current_user
from security.ownership import ensure_owner

router = APIRouter(tags=["predict"])

# Histórico de predições em memória: {prediction_id: {"owner": ..., "response": ...}}.
# Mesma ressalva de security/users.py — será trocado por persistência real
# (SQLModel) em etapa futura. IDs são UUID4 (não sequenciais), o que já
# dificulta a enumeração; a checagem de ownership em GET /predictions/{id}
# é o controle de BOLA propriamente dito.
_PREDICTIONS: dict[str, dict] = {}
_lock = Lock()


_AUTH_ERRORS = {401: {"description": "Token ausente, inválido ou expirado"}}


@router.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        **_AUTH_ERRORS,
        422: {"description": "Corpo inválido: campo ausente, vazio, longo demais, tipo errado ou campo extra"},
    },
)
def predict(
    request: PredictRequest,
    current_user: User = Depends(get_current_user),
) -> PredictResponse:
    """Infere a intenção de um ticket e grava a predição no histórico do
    usuário autenticado.

    **Placeholder:** o modelo de classificação ainda não foi integrado. A
    resposta é sempre `intent="Technical issue"` com `confidence=0.0` — o
    0.0 indica que não houve inferência real (ver `PredictResponse`).
    """
    response = PredictResponse(
        id=str(uuid4()), intent=Intent.TECHNICAL_ISSUE, confidence=0.0
    )
    with _lock:
        _PREDICTIONS[response.id] = {
            "owner": current_user.username,
            "response": response,
        }
    return response


@router.get(
    "/predictions/{prediction_id}",
    response_model=PredictResponse,
    responses={
        **_AUTH_ERRORS,
        404: {"description": "Predição inexistente ou pertencente a outro usuário"},
    },
)
def get_prediction(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
) -> PredictResponse:
    """Retorna uma predição do histórico, somente se pertencer ao usuário
    autenticado (checagem BOLA)."""
    record = _PREDICTIONS.get(prediction_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado",
        )
    # Checagem BOLA: mesmo 404 do caso "não existe" — ver security/ownership.py.
    ensure_owner(record["owner"], current_user)
    return record["response"]
