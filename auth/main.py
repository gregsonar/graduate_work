from contextlib import asynccontextmanager

import uvicorn
from api.v1 import auth_api, role_api
from core.config import config
from core.middleware.http import setup_middleware
from core.tracer import configure_tracer
from db import redis_db
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from redis.asyncio import Redis

from auth.api.v1.oauth.base_oauth_router import vk_router, yandex_router
from auth.db.redis_db import get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):

    redis_client = redis_db.get_redis()
    yield
    await redis_client.close()


# Настраиваем Jaeger-трейсер
configure_tracer()

app = FastAPI(
    title=config.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 configuration for Swagger UI
app.swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
    "persistAuthorization": True,
}

# OpenAPI security scheme configuration
app.openapi_components = {
    "securitySchemes": {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите ваш JWT токен в формате: **Bearer &lt;token&gt;**\n\n"
            "Например: Bearer eyJhbGciOiJIUzI1NiIs...",
        }
    }
}

# Apply security globally to all endpoints that require authentication
app.openapi_security = [{"bearerAuth": []}]

setup_middleware(app, get_redis())
RequestsInstrumentor().instrument()
FastAPIInstrumentor.instrument_app(app)

# Теги указываем для удобства навигации по документации
app.include_router(role_api.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(auth_api.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(vk_router, prefix="/api/v1/auth")
app.include_router(yandex_router, prefix="/api/v1/auth")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info", reload=True)
