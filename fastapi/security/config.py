"""Configuração central da API, lida do ambiente (arquivo .env via
python-dotenv). Todo valor ajustável por ambiente é definido AQUI — os
demais módulos apenas importam as constantes, nunca chamam os.getenv.

Seções:
  1. Autenticação (JWT + OAuth2PasswordBearer)
  2. CORS
  3. Rate limiting de POST /auth/token
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --- 1. Autenticação (JWT + OAuth2PasswordBearer) ---
# Fluxo: o cliente envia username/password (form) para AUTH_TOKEN_URL,
# recebe um JWT assinado com JWT_SECRET_KEY e o reenvia nas rotas
# protegidas no header "Authorization: Bearer <token>". Detalhes em
# SECURITY.md, seção "Autenticação".

# Rota de emissão de token. Usada tanto pelo router (routes/auth.py)
# quanto pelo OAuth2PasswordBearer (security/oauth2.py, que a anuncia no
# OpenAPI/Swagger) — um único lugar evita que as duas divirjam.
AUTH_ROUTER_PREFIX = "/auth"
AUTH_TOKEN_PATH = "/token"
AUTH_TOKEN_URL = f"{AUTH_ROUTER_PREFIX}{AUTH_TOKEN_PATH}".lstrip("/")

# Algoritmo fixo (não configurável): o decode aceita SOMENTE este
# algoritmo, o que impede ataques de troca de algoritmo (ex.: "alg": "none").
JWT_ALGORITHM = "HS256"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY não está definida no ambiente. Defina-a (ex.: via "
        "arquivo .env) antes de iniciar a aplicação."
    )

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("JWT_EXPIRE_MINUTES deve ser um inteiro positivo.")

# --- 2. CORS ---
# Allowlist explícita de origens autorizadas a consumir a API a partir de
# um browser (ver main.py, CORSMiddleware). Formato: origens separadas
# por vírgula, ex. "https://app.exemplo.com,https://admin.exemplo.com".
# Nunca usar "*" em produção — e nunca combinar "*" com
# allow_credentials=True (não é o caso aqui: a API autentica via Bearer
# token no header Authorization, não via cookies).
_raw_allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [
    origin.strip() for origin in _raw_allowed_origins.split(",") if origin.strip()
]

# --- 3. Rate limiting (POST /auth/token) ---
# Ver security/rate_limit.py para a justificativa completa da escolha
# destes valores (5 tentativas / 60s, por IP e por username).
AUTH_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "5"))
AUTH_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60"))
