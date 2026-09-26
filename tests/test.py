import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fastapi"))

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from main import app
from models.user import User
from security.ownership import ensure_owner
from security.jwt import create_access_token

client = TestClient(app)


# (a) Tentativa de acesso sem token
def test_predict_without_token():
    response = client.post(
        "/predict",
        json={
            "ticket_subject": "Problema técnico",
            "ticket_description": "Meu produto não está funcionando.",
        },
    )

    assert response.status_code == 401


# (b) Tentativa de acesso ao recurso de outro usuário
def test_cannot_access_resource_of_another_user():
    current_user = User(username="user_a")

    with pytest.raises(HTTPException) as exc_info:
        ensure_owner(
            resource_owner_username="user_b",
            current_user=current_user,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Recurso não encontrado"


# (c) Envio de campo extra no body
def test_predict_rejects_extra_body_field():
    token = create_access_token({"sub": "admin"})

    response = client.post(
        "/predict",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "ticket_subject": "Problema técnico",
            "ticket_description": "Meu produto não está funcionando.",
            "is_admin": True,
        },
    )

    assert response.status_code == 422