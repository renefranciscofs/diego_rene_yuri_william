"""Testes de segurança da API (pytest + TestClient do FastAPI).

Execução, a partir da raiz do repositório:  pytest tests/ -v
Setup comum (sys.path, JWT_SECRET_KEY, reset de estado, tokens) em conftest.py.
"""

import base64
import json
from datetime import timedelta

import pytest

from security.jwt import create_access_token

VALID_TICKET = {
    "ticket_subject": "Problema técnico",
    "ticket_description": "Meu produto não está funcionando.",
}


def login(client, username, password):
    return client.post(
        "/auth/token", data={"username": username, "password": password}
    )


# ---------------------------------------------------------------------------
# 1. Autenticação — credenciais válidas e inválidas
# ---------------------------------------------------------------------------


def test_login_with_valid_credentials_returns_bearer_token(client):
    response = login(client, "admin", "admin123")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


@pytest.mark.parametrize(
    "username, password",
    [
        ("admin", "senha-errada"),  # usuário existe, senha errada
        ("nao-existe", "admin123"),  # usuário inexistente
    ],
)
def test_login_with_invalid_credentials_returns_401(client, username, password):
    response = login(client, username, password)

    assert response.status_code == 401
    # Mesma mensagem nos dois casos: não revela se o usuário existe.
    assert response.json()["detail"] == "Usuário ou senha incorretos"
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert "access_token" not in response.json()


# ---------------------------------------------------------------------------
# 2. Autorização / BOLA — usuário A não acessa recurso do usuário B
# ---------------------------------------------------------------------------


def test_owner_can_read_own_prediction(client, admin_headers):
    created = client.post("/predict", json=VALID_TICKET, headers=admin_headers)
    assert created.status_code == 200
    prediction_id = created.json()["id"]

    response = client.get(f"/predictions/{prediction_id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == created.json()


def test_user_cannot_read_prediction_of_another_user(
    client, admin_headers, analista_headers
):
    created = client.post("/predict", json=VALID_TICKET, headers=admin_headers)
    assert created.status_code == 200
    prediction_id = created.json()["id"]

    # "analista" está autenticado, mas o recurso pertence a "admin".
    response = client.get(f"/predictions/{prediction_id}", headers=analista_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Recurso não encontrado"}
    assert "intent" not in response.json()


def test_bola_response_is_indistinguishable_from_missing_resource(
    client, admin_headers, analista_headers
):
    """404 idêntico para 'é de outro usuário' e 'não existe': impede
    enumerar IDs válidos de outros usuários."""
    created = client.post("/predict", json=VALID_TICKET, headers=admin_headers)
    other_users_id = created.json()["id"]

    foreign = client.get(f"/predictions/{other_users_id}", headers=analista_headers)
    missing = client.get("/predictions/id-inexistente", headers=analista_headers)

    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()


# ---------------------------------------------------------------------------
# 3. Validação de entrada — Pydantic (extra='forbid', tipos, tamanhos)
# ---------------------------------------------------------------------------


def test_predict_rejects_extra_body_field(client, admin_headers):
    payload = {**VALID_TICKET, "is_admin": True}

    response = client.post("/predict", json=payload, headers=admin_headers)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        err["type"] == "extra_forbidden" and err["loc"][-1] == "is_admin"
        for err in errors
    )


@pytest.mark.parametrize(
    "payload, bad_field",
    [
        ({"ticket_subject": "Assunto"}, "ticket_description"),  # campo obrigatório ausente
        ({**VALID_TICKET, "ticket_subject": ""}, "ticket_subject"),  # min_length=1
        ({**VALID_TICKET, "ticket_subject": "x" * 201}, "ticket_subject"),  # max_length=200
        ({**VALID_TICKET, "ticket_description": 123}, "ticket_description"),  # tipo errado
    ],
)
def test_predict_rejects_invalid_input(client, admin_headers, payload, bad_field):
    response = client.post("/predict", json=payload, headers=admin_headers)

    assert response.status_code == 422
    assert any(err["loc"][-1] == bad_field for err in response.json()["detail"])


def test_predict_accepts_valid_input(client, admin_headers):
    response = client.post("/predict", json=VALID_TICKET, headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "intent", "confidence"}
    assert 0.0 <= body["confidence"] <= 1.0


def test_predict_placeholder_contract(client, admin_headers):
    """Contrato documentado do placeholder: intenção fixa com confidence
    0.0 (sinaliza que não houve inferência real)."""
    response = client.post("/predict", json=VALID_TICKET, headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["intent"] == "Technical issue"
    assert response.json()["confidence"] == 0.0


# ---------------------------------------------------------------------------
# 4. Rate limiting — POST /auth/token (5 tentativas / 60s)
# ---------------------------------------------------------------------------


def test_login_rate_limit_returns_429_after_limit(client):
    # As 5 primeiras tentativas (limite configurado) são processadas
    # normalmente — aqui com senha errada, simulando brute force.
    for _ in range(5):
        response = login(client, "admin", "senha-errada")
        assert response.status_code == 401

    # A 6ª é bloqueada antes mesmo de verificar a senha — inclusive com a
    # senha correta, o que mostra que o atacante não ganha nada insistindo.
    blocked = login(client, "admin", "admin123")

    assert blocked.status_code == 429
    assert blocked.json()["detail"] == (
        "Muitas tentativas de login. Tente novamente em instantes."
    )
    assert blocked.headers["Retry-After"] == "60"
    assert "access_token" not in blocked.json()


# ---------------------------------------------------------------------------
# 5. Rota protegida — sem token / token inválido / expirado
# ---------------------------------------------------------------------------


def test_predict_without_token_returns_401(client):
    response = client.post("/predict", json=VALID_TICKET)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_prediction_without_token_returns_401(client):
    response = client.get("/predictions/qualquer-id")

    assert response.status_code == 401


@pytest.mark.parametrize(
    "token",
    [
        "token-malformado",
        # Assinado com outra chave (token forjado).
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJhZG1pbiJ9."
        "c2lnbmF0dXJhLWZhbHNh",
    ],
)
def test_predict_with_invalid_token_returns_401(client, token):
    response = client.post(
        "/predict", json=VALID_TICKET, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Não foi possível validar as credenciais"}


def test_predict_with_expired_token_returns_401(client):
    expired = create_access_token({"sub": "admin"}, expires_delta=timedelta(minutes=-1))

    response = client.post(
        "/predict", json=VALID_TICKET, headers={"Authorization": f"Bearer {expired}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Não foi possível validar as credenciais"}


def test_predict_with_token_for_unknown_user_returns_401(client):
    """Token com assinatura válida, mas para um usuário que não existe."""
    token = create_access_token({"sub": "usuario-fantasma"})

    response = client.post(
        "/predict", json=VALID_TICKET, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def _b64url(data: dict) -> str:
    raw = json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def test_predict_with_alg_none_token_returns_401(client):
    """Token sem assinatura ("alg": "none"): o decode só aceita HS256."""
    token = f'{_b64url({"alg": "none", "typ": "JWT"})}.{_b64url({"sub": "admin"})}.'

    response = client.post(
        "/predict", json=VALID_TICKET, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Não foi possível validar as credenciais"}


def test_predict_with_token_without_sub_returns_401(client):
    """Token com assinatura válida, mas sem a claim "sub" (identidade)."""
    token = create_access_token({"role": "admin"})

    response = client.post(
        "/predict", json=VALID_TICKET, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401

