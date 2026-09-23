from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth, health, predict
from security.config import ALLOWED_ORIGINS
from security.headers import SecurityHeadersMiddleware

app = FastAPI(
    title="Sistema de Atendimento ao Cliente com IA",
    description="API que infere a intenção por trás de um ticket de suporte.",
    version="0.1.0",
)

# CORS: allowlist explícita de origens configurada via ALLOWED_ORIGINS
# (.env). allow_credentials=False porque a autenticação é via Bearer
# token no header Authorization, não via cookies — ver security/config.py.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Headers de segurança (HSTS, X-Frame-Options, X-Content-Type-Options,
# CSP, Referrer-Policy) em toda resposta — ver security/headers.py.
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
