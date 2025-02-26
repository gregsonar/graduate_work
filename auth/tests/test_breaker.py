# auth/tests/test_breaker.py
import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from auth.core.breaker import CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_initial_state(circuit_breaker, mock_redis_client):
    """Test initial circuit breaker state"""
    mock_redis_client.get.return_value = None
    state = await circuit_breaker.get_state()
    assert state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(
    circuit_breaker, mock_service, mock_redis_client
):
    """Test circuit breaker opens after threshold failures"""
    state_key = f"{circuit_breaker._prefix}:state"
    failures_key = f"{circuit_breaker._prefix}:failures"

    # Словарь для хранения состояния мока
    mock_state = {"failure_count": 0}

    async def mock_get(key):
        if key == failures_key:
            # Увеличиваем счетчик ошибок при каждом вызове
            mock_state["failure_count"] += 1
            return str(mock_state["failure_count"]).encode()
        elif key == state_key:
            # Возвращаем OPEN когда достигнут порог ошибок
            return (
                b"OPEN"
                if mock_state["failure_count"] >= circuit_breaker.failure_threshold
                else None
            )
        return None

    async def mock_set(*args, **kwargs):
        return True

    # Настраиваем mock.get и mock.set
    mock_redis_client.get = AsyncMock(side_effect=mock_get)
    mock_redis_client.set = AsyncMock(side_effect=mock_set)

    # Настраиваем pipeline
    pipeline_mock = AsyncMock()
    pipeline_mock.set = AsyncMock(return_value=pipeline_mock)
    pipeline_mock.execute = AsyncMock(return_value=[True, True])
    mock_redis_client.pipeline = AsyncMock(return_value=pipeline_mock)

    protected_operation = circuit_breaker(mock_service.test_operation)
    mock_service.should_fail = True

    # Call operation until failure threshold
    for _ in range(circuit_breaker.failure_threshold):
        with pytest.raises(Exception):
            await protected_operation()

    # Проверяем состояние после ошибок
    state = await circuit_breaker.get_state()
    assert state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_fallback(
    circuit_breaker, mock_service, mock_redis_client
):
    """Test fallback mechanism when circuit is open"""
    responses = {
        f"{circuit_breaker._prefix}:state": b"OPEN",
        f"{circuit_breaker._prefix}:last_failure": str(
            asyncio.get_event_loop().time()
        ).encode(),
        f"auth_token_cache:test_user": None,
    }

    def mock_get(key):
        return responses.get(key, None)

    mock_redis_client.get.side_effect = mock_get
    mock_service.should_fail = True

    protected_operation = circuit_breaker(mock_service.test_operation)
    result = await protected_operation("test_user")

    assert result["access_token"] == "guest_token"
    assert result["refresh_token"] is None
    assert result["permissions"] == ["read_basic"]


@pytest.mark.asyncio
async def test_circuit_breaker_recovery(
    circuit_breaker, mock_service, mock_redis_client
):
    """Test circuit breaker recovery through half-open state"""
    current_time = asyncio.get_event_loop().time()
    old_failure_time = current_time - circuit_breaker.recovery_timeout - 1

    responses = {
        f"{circuit_breaker._prefix}:state": b"OPEN",
        f"{circuit_breaker._prefix}:last_failure": str(old_failure_time).encode(),
        f"{circuit_breaker._prefix}:half_open_tries": b"0",
    }

    def mock_get(key):
        return responses.get(key, None)

    # Настраиваем моки
    mock_redis_client.get.side_effect = mock_get
    mock_redis_client.set = AsyncMock()
    mock_redis_client.incr = AsyncMock(return_value=1)
    mock_redis_client.delete = AsyncMock()

    mock_service.should_fail = False

    protected_operation = circuit_breaker(mock_service.test_operation)

    # First operation in HALF-OPEN
    result = await protected_operation()
    assert result["access_token"] == "test_token"

    # Проверяем что set был вызван для установки HALF-OPEN состояния
    mock_redis_client.set.assert_called()

    # Reset mock для следующей проверки
    mock_redis_client.set.reset_mock()

    # Update state to HALF-OPEN after success
    responses[f"{circuit_breaker._prefix}:state"] = b"HALF_OPEN"

    # Second operation should succeed
    result = await protected_operation()
    assert result["access_token"] == "test_token"

    # Verify state transitions
    mock_redis_client.set.assert_called()


@pytest.mark.asyncio
async def test_circuit_breaker_token_caching(
    circuit_breaker, mock_service, mock_redis_client
):
    """Test token caching mechanism"""
    test_token = {"access_token": "test_token", "refresh_token": "refresh"}

    cache_key = f"auth_token_cache:test_user"
    cached_value = json.dumps(test_token).encode()

    # First call - cache miss
    mock_redis_client.get.return_value = None
    protected_operation = circuit_breaker(mock_service.test_operation)

    result = await protected_operation(user_id="test_user")
    assert result["access_token"] == "test_token"

    # Second call - cache hit
    mock_redis_client.get.return_value = cached_value
    result = await protected_operation(user_id="test_user")
    assert result["access_token"] == "test_token"

    # Verify cache operations
    mock_redis_client.setex.assert_called()
