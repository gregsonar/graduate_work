from uuid import UUID
import pytest
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from opentelemetry.trace import SpanKind
from auth.core.middleware.request_limit import RequestLimit
from auth.core.middleware.tracker import RequestTracker
from auth.core.middleware.http import request_limit_middleware

pytestmark = pytest.mark.asyncio


async def test_rate_limiter_basic(context_redis_client):
    """Test basic rate limiting functionality"""
    limiter = RequestLimit(context_redis_client)

    pipeline = context_redis_client.pipeline.return_value
    pipeline.execute.return_value = [1, True]  # First request

    # First request should not be limited
    is_limited, remaining = await limiter.is_rate_limit("test_key", 5, 60)
    assert not is_limited
    assert remaining == 4

    # Verify Redis calls
    context_redis_client.pipeline.assert_called_once()
    pipeline.incr.assert_called_once()
    pipeline.expire.assert_called_once()


async def test_rate_limiter_exceeds_limit(context_redis_client):
    """Test rate limiting when limit is exceeded"""
    limiter = RequestLimit(context_redis_client)

    pipeline = context_redis_client.pipeline.return_value
    pipeline.execute.return_value = [6, True]  # Return value > max_requests

    is_limited, remaining = await limiter.is_rate_limit("test_key", 5, 60)
    assert is_limited
    assert remaining <= 0


async def test_request_tracker_generate_request_id():
    """Test request ID generation when header is missing"""
    tracker = RequestTracker()
    mock_request = Request(
        scope={"type": "http", "headers": [], "method": "GET", "path": "/test"}
    )

    request_id = tracker.get_or_generate_request_id(mock_request)
    assert isinstance(UUID(request_id), UUID)  # Verify it's a valid UUID


async def test_request_tracker_existing_request_id():
    """Test request ID extraction from headers"""
    tracker = RequestTracker()
    test_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_request = Request(
        scope={
            "type": "http",
            "headers": [(b"x-request-id", test_id.encode())],
            "method": "GET",
            "path": "/test",
        }
    )

    request_id = tracker.get_or_generate_request_id(mock_request)
    assert request_id == test_id


async def test_request_tracker_setup_tracing():
    """Test tracing setup with OpenTelemetry"""
    tracker = RequestTracker()
    mock_request = Request(
        scope={"type": "http", "headers": [], "method": "GET", "path": "/test"}
    )

    # Setup tracing
    tracker.setup_tracing(mock_request, "test-request-id")

    # Verify span was created with correct attributes
    # Note: This is a basic verification, as we can't easily mock OpenTelemetry's global tracer


async def test_middleware_auth_endpoint_rate_limit(context_redis_client):
    """Test rate limiting for auth endpoints"""
    limiter = RequestLimit(context_redis_client)
    tracker = RequestTracker()

    pipeline = context_redis_client.pipeline.return_value
    pipeline.execute.return_value = [6, True]  # Exceeding limit

    mock_request = Request(
        scope={
            "type": "http",
            "headers": [],
            "method": "POST",
            "path": "/api/v1/auth/login",
            "client": ("127.0.0.1", 1234),
        }
    )

    async def mock_call_next(request):
        return JSONResponse(content={"status": "ok"})

    response = await request_limit_middleware(
        request=mock_request, call_next=mock_call_next, limiter=limiter, tracker=tracker
    )

    assert response.status_code == 429
    assert "X-Request-Id" in response.headers


async def test_middleware_auth_endpoint_rate_limit(mock_redis_client):
    """Test rate limiting for auth endpoints"""
    app = FastAPI()
    limiter = RequestLimit(mock_redis_client)
    tracker = RequestTracker()

    # Configure Redis mock to simulate exceeding limit
    pipeline = await mock_redis_client.pipeline()
    pipeline.execute.return_value = [6, True]  # Return value > max_requests

    mock_request = Request(
        scope={
            "type": "http",
            "headers": [],
            "method": "POST",
            "path": "/api/v1/auth/login",
            "client": ("127.0.0.1", 1234),
        }
    )

    async def mock_call_next(request):
        return JSONResponse(content={"status": "ok"})

    response = await request_limit_middleware(
        request=mock_request, call_next=mock_call_next, limiter=limiter, tracker=tracker
    )

    assert response.status_code == 429
    assert "X-Request-Id" in response.headers


async def test_middleware_headers(mock_redis_client):
    """Test response headers set by middleware"""
    app = FastAPI()
    limiter = RequestLimit(mock_redis_client)
    tracker = RequestTracker()

    mock_request = Request(
        scope={
            "type": "http",
            "headers": [],
            "method": "POST",
            "path": "/api/v1/auth/login",
            "client": ("127.0.0.1", 1234),
        }
    )

    pipeline = await mock_redis_client.pipeline()
    pipeline.execute.return_value = [1, True]  # First request, under limit

    async def mock_call_next(request):
        return JSONResponse(content={"status": "ok"})

    response = await request_limit_middleware(
        request=mock_request, call_next=mock_call_next, limiter=limiter, tracker=tracker
    )

    assert "X-Request-Id" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert response.headers["X-RateLimit-Remaining"] == "4"  # 5 - 1
