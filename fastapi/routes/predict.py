from fastapi import APIRouter, Depends

from models.predict import Intent, PredictRequest, PredictResponse
from models.user import User
from security.oauth2 import get_current_user

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
def predict(
    request: PredictRequest,
    current_user: User = Depends(get_current_user),
) -> PredictResponse:
    # Placeholder: o modelo de classificação de intenção será integrado em
    # uma etapa futura do projeto. Por ora, retorna uma resposta fixa apenas
    # para validar o contrato da rota (autenticação + schemas de entrada/saída).
    return PredictResponse(intent=Intent.TECHNICAL_ISSUE, confidence=0.0)
