"""Camada HTTP: define os endpoints (APIRouter) e orquestra a requisição.

As rotas não implementam regras de segurança nem validação por conta
própria — recebem corpos já validados de `models/` e aplicam controles de
`security/` via `Depends(...)`.

- `health.py`  — GET /health (disponibilidade, público).
- `auth.py`    — POST /auth/token, com rate limit.
- `predict.py` — POST /predict e GET /predictions/{id} (protegidas por JWT; ownership/BOLA).
"""
