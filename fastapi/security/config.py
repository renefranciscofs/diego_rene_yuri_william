import os

from dotenv import load_dotenv

load_dotenv()

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY não está definida no ambiente. Defina-a (ex.: via "
        "arquivo .env) antes de iniciar a aplicação."
    )

# --- CORS ---
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

# --- Rate limiting (POST /auth/token) ---
# Ver security/rate_limit.py para a justificativa completa da escolha
# destes valores (5 tentativas / 60s, por IP e por username).
AUTH_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "5"))
AUTH_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60"))
