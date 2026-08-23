from fastapi import FastAPI

from routes import auth, health, predict

app = FastAPI(
    title="Sistema de Atendimento ao Cliente com IA",
    description="API que infere a intenção por trás de um ticket de suporte.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
