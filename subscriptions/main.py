import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from subscriptions.api.v1 import subscription_router
from subscriptions.core.config import settings
from subscriptions.middlewares.auth_middleware import (
    AuthConfig,
    AuthMiddleware,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    root_path="/api/subscriptions",
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
            "description": "Введите ваш JWT токен в формате: **Bearer &lt;token&gt;**\n\n"
            "Например: Bearer eyJhbGciOiJIUzI1NiIs...",
        }
    }
}

app.openapi_security = [{"bearerAuth": []}]


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(
    subscription_router.router, prefix="/api/v1/subscription", tags=["subscription"]
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info", reload=True)
