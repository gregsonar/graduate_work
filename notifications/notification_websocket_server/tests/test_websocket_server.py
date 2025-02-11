import asyncio
import json
import uuid
from unittest import mock
import pytest
from websockets.exceptions import ConnectionClosed

from notifications.notification_websocket_server.websocket import WebSocketServer, Message, MessageType

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_db_pool():
    pool = mock.AsyncMock()
    conn = mock.AsyncMock()
    conn.execute = mock.AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.close = mock.AsyncMock()
    return pool

@pytest.fixture
async def mock_rabbit_connection():
    connection = mock.AsyncMock()
    channel = mock.AsyncMock()
    connection.channel.return_value = channel
    connection.close = mock.AsyncMock()
    return connection

@pytest.fixture
async def websocket_server(mock_db_pool, mock_rabbit_connection):
    server = WebSocketServer(host="localhost", port=8765)
    server.rabbit_connection = mock_rabbit_connection
    server.db_pool = mock_db_pool
    server.connections = {}
    server.pending_messages = {}
    await server.initialize()
    return server

@pytest.fixture
def user_id():
    return uuid.uuid4()

@pytest.fixture
def mock_websocket():
    websocket = mock.AsyncMock()
    return websocket

@pytest.mark.asyncio
async def test_authenticate_client_success(websocket_server, mock_websocket, user_id):
    mock_websocket.recv.return_value = str(user_id)
    
    result = await websocket_server._authenticate_client(mock_websocket)
    
    assert result == user_id
    mock_websocket.send.assert_called_once_with(json.dumps({"status": "connected"}))

@pytest.mark.asyncio
async def test_authenticate_client_invalid_uuid(websocket_server, mock_websocket):
    mock_websocket.recv.return_value = "invalid-uuid"
    
    with pytest.raises(ValueError):
        await websocket_server._authenticate_client(mock_websocket)

@pytest.mark.asyncio
async def test_handle_client_messages_status_update(websocket_server, mock_websocket, user_id):
    message = Message(
        type=MessageType.STATUS,
        payload={"status": "read"},
        user_id=user_id,
        message_id=uuid.uuid4()
    )
    mock_websocket.__aiter__.return_value = [message.to_json()]
    websocket_server.pending_messages[user_id] = {message.message_id}
    
    await websocket_server._handle_client_messages(mock_websocket, user_id)
    
    assert message.message_id not in websocket_server.pending_messages.get(user_id, set())

@pytest.mark.asyncio
async def test_deliver_notification(websocket_server, mock_websocket, user_id):
    notification_data = json.dumps({"content": "test notification"}).encode()
    websocket_server.connections[user_id] = mock_websocket
    websocket_server.pending_messages[user_id] = set()
    
    await websocket_server._deliver_notification(user_id, notification_data)
    
    mock_websocket.send.assert_called_once()
    assert len(websocket_server.pending_messages[user_id]) == 1

@pytest.mark.asyncio
async def test_cleanup_connection(websocket_server, user_id):
    websocket_server.connections[user_id] = mock.AsyncMock()
    websocket_server.pending_messages[user_id] = set()
    
    await websocket_server._cleanup_connection(user_id)
    
    assert user_id not in websocket_server.connections
    assert user_id not in websocket_server.pending_messages

@pytest.mark.asyncio
async def test_handle_status_update(websocket_server, user_id):
    message_id = uuid.uuid4()
    message = Message(
        type=MessageType.STATUS,
        payload={"status": "read"},
        user_id=user_id,
        message_id=message_id
    )
    websocket_server.pending_messages[user_id] = {message_id}
    
    await websocket_server._handle_status_update(message)
    
    assert message_id not in websocket_server.pending_messages[user_id]
    assert websocket_server.db_pool.acquire.called 