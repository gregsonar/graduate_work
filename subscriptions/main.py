import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from subscriptions.core.config import settings
from subscriptions.api.v1 import subscription_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    # lifespan=lifespan,

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(subscription_router.router, prefix='/api/v1/subscription', tags=['subscription'])



if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8001, log_level='info', reload=True)