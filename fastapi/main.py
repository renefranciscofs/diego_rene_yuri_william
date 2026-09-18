from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware 
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from routes import auth, health, predict
from routes.auth import limiter as auth_limiter

app = FastAPI(
    title="Sistema de Atendimento ao Cliente com IA",
    description="API que infere a intenção por trás de um ticket de suporte.",
    version="0.1.0",
)
app.state.limiter = auth_limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

allow_list = [
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers['Strict-Transport-Security'] = ("max-age=31536000; includeSubDomains")
    response.headers["X-Frame-Options"] = "Deny"
    response.headers['X-Content-Type-Options'] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self'"
    )

    return response
    
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
