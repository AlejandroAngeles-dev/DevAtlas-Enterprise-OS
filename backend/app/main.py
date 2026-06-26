import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="DevAtlas Enterprise OS",
    description="Sistema operativo inteligente para PYMEs",
    version="1.0.0",
)

# CORS — permite que el frontend en localhost:3000 haga requests al backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/api")