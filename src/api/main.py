from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from src.api.router import router
from src.config.settings import settings
from src.db.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Создаем приложение
app = FastAPI(
    title="KreditScore API",
    description="API для сервиса оценки долговой нагрузки и скоринга",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://kreditscore.uz"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(router, prefix="/api/v1")

# Метрики Prometheus
if settings.metrics_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/", tags=["root"])
async def root():
    """Корневой эндпоинт"""
    return {
        "name": "KreditScore API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}