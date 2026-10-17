import os
import sys
from pathlib import Path

# O código da API vive em fastapi/ e usa imports absolutos (`from routes ...`).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fastapi"))

# Valores fixos para os testes, definidos ANTES de importar a app:
# security/config.py lê o ambiente no import (e falha sem JWT_SECRET_KEY).
# load_dotenv() não sobrescreve variáveis já definidas, então o .env local
# não interfere nos testes.
os.environ["JWT_SECRET_KEY"] = "test-secret-key-somente-para-pytest"
os.environ["AUTH_RATE_LIMIT_MAX_ATTEMPTS"] = "5"
os.environ["AUTH_RATE_LIMIT_WINDOW_SECONDS"] = "60"

import pytest
from fastapi.testclient import TestClient

from main import app
from routes import predict as predict_route
from security import rate_limit


@pytest.fixture(autouse=True)
def reset_state():
    """Zera o estado em memória (contadores de rate limit e histórico de
    predições) antes e depois de cada teste, para que os testes sejam
    independentes da ordem de execução."""
    rate_limit._attempts_by_key.clear()
    predict_route._PREDICTIONS.clear()
    yield
    rate_limit._attempts_by_key.clear()
    predict_route._PREDICTIONS.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def login(client: TestClient, username: str, password: str):
    return client.post(
        "/auth/token", data={"username": username, "password": password}
    )


def auth_header(client: TestClient, username: str, password: str) -> dict:
    response = login(client, username, password)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def admin_headers(client) -> dict:
    return auth_header(client, "admin", "admin123")


@pytest.fixture
def analista_headers(client) -> dict:
    return auth_header(client, "analista", "analista123")
