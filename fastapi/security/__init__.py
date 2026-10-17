"""Controles de segurança, reutilizados pelas rotas via `Depends`.

- `config.py`     — configuração central lida do .env (JWT, CORS, rate limit).
- `jwt.py`        — emissão e validação do token JWT (HS256, com expiração).
- `oauth2.py`     — OAuth2PasswordBearer + `get_current_user` (401 para token ausente/inválido/expirado).
- `users.py`      — base de usuários em memória e verificação de senha (bcrypt).
- `ownership.py`  — `ensure_owner`: checagem BOLA (404 para recurso de outro usuário).
- `rate_limit.py` — limite de tentativas em /auth/token (429 + Retry-After).
- `headers.py`    — middleware de headers de segurança HTTP (HSTS, CSP, ...).
"""
