from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from models.token import Token
from security.jwt import create_access_token
from security.rate_limit import check_rate_limit, enforce_auth_rate_limit
from security.users import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=Token,
    dependencies=[Depends(enforce_auth_rate_limit)],
)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    # Segunda dimensão do rate limit: por username, além do limite por
    # IP já aplicado pela dependency `enforce_auth_rate_limit` acima.
    # Justificativa completa em security/rate_limit.py.
    check_rate_limit(f"user:{form_data.username}")

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return Token(access_token=access_token)
