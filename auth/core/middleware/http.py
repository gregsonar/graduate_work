from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import ORJSONResponse

from .request_limit import RequestLimit
from .tracker import RequestTracker


async def request_limit_middleware(
    request: Request,
    call_next: Callable,
    limiter: RequestLimit,
    tracker: RequestTracker,
) -> ORJSONResponse | Response:
    request_id = tracker.get_or_generate_request_id(request)
    tracker.setup_tracing(request, request_id)

    if not request.url.path.startswith("/api/v1/auth"):
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    client_ip = request.client.host

    if request.url.path == "/api/v1/auth/login":
        is_limited, remaining = await limiter.is_rate_limit(
            f"{client_ip}:login", max_requests=5, window=300
        )
    else:
        is_limited, remaining = await limiter.is_rate_limit(
            f"{client_ip}:auth", max_requests=30, window=60
        )

    if is_limited:
        return ORJSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests", "request_id": request_id},
        )

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    return response


def setup_middleware(app: FastAPI, redis_client) -> None:

    limiter = RequestLimit(redis_client)
    tracker = RequestTracker()

    @app.middleware("http")
    async def middleware(request: Request, call_next: Callable) -> Response:
        return await request_limit_middleware(request, call_next, limiter, tracker)
