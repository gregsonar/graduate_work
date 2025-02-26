from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import create_async_engine

from billing.src.api import healthcheck
from billing.src.api.v1 import billing, tariffs
from billing.src.core.config import settings
from billing.src.core.exceptions import BaseErrorWithContent
from billing.src.db import postgres


@asynccontextmanager
async def lifespan(app: FastAPI):
    postgres.engine = create_async_engine(settings.dsn, future=True)
    yield
    await postgres.engine.dispose()


app = FastAPI(
    title="BillingService",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    root_path="/api/billing",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

app.swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
    "persistAuthorization": True,
}

app.openapi_components = {
    "securitySchemes": {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите ваш JWT токен в формате:"
            " **Bearer &lt;token&gt;**\n\n"
            "Например: Bearer eyJhbGciOiJIUzI1NiIs...",
        }
    }
}

app.openapi_security = [{"bearerAuth": []}]


@app.exception_handler(BaseErrorWithContent)
async def project_error_handler(request: Request, exc: BaseErrorWithContent):
    return ORJSONResponse(
        status_code=exc.status_code,
        content=exc.content,
    )


app.include_router(healthcheck.router, prefix="/api/v1/billing", tags=["health"])
app.include_router(tariffs.router, prefix="/api/v1/billing", tags=["tariffs"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])
