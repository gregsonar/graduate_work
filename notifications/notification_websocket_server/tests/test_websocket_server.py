import asyncio
import json
import uuid
from unittest import mock
import pytest
from websockets.exceptions import ConnectionClosed

from notifications.notification_websocket_server.websocket import WebSocketServer, Message, MessageType

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture
async def mock_db_pool():
    pool = mock.AsyncMock()
    conn = mock.AsyncMock()
    conn.execute = mock.AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool

@pytest.fixture
async def websocket_server(mock_db_pool):
    server = WebSocketServer(host="localhost", port=8765)
    # Мокаем подключение к RabbitMQ и БД
    server.rabbit_connection = mock.AsyncMock()
    server.db_pool = mock_db_pool
    server.connections = {}
    server.pending_messages = {}
    await server.initialize()  # Инициализируем сервер
    yield server
    # Закрываем соединения
    if server.rabbit_connection:
        await server.rabbit_connection.close()
    if server.db_pool:
        await server.db_pool.close()

@pytest.fixture
def user_id():
    return uuid.uuid4()

@pytest.fixture
def mock_websocket():
    websocket = mock.AsyncMock()
    return websocket

@pytest.mark.asyncio
async def test_authenticate_client_success(websocket_server, mock_websocket, user_id):
    async for server in websocket_server:
        mock_websocket.recv.return_value = str(user_id)
        
        result = await server._authenticate_client(mock_websocket)
        
        assert result == user_id
        mock_websocket.send.assert_called_once_with(json.dumps({"status": "connected"}))

@pytest.mark.asyncio
async def test_authenticate_client_invalid_uuid(websocket_server, mock_websocket):
    async for server in websocket_server:
        mock_websocket.recv.return_value = "invalid-uuid"
        
        with pytest.raises(ValueError):
            await server._authenticate_client(mock_websocket)

@pytest.mark.asyncio
async def test_handle_client_messages_status_update(websocket_server, mock_websocket, user_id):
    async for server in websocket_server:
        message = Message(
            type=MessageType.STATUS,
            payload={"status": "read"},
            user_id=user_id,
            message_id=uuid.uuid4()
        )
        mock_websocket.__aiter__.return_value = [message.to_json()]
        server.pending_messages[user_id] = {message.message_id}
        
        await server._handle_client_messages(mock_websocket, user_id)
        
        assert message.message_id not in server.pending_messages.get(user_id, set())

@pytest.mark.asyncio
async def test_deliver_notification(websocket_server, mock_websocket, user_id):
    async for server in websocket_server:
        notification_data = json.dumps({"content": "test notification"}).encode()
        server.connections[user_id] = mock_websocket
        server.pending_messages[user_id] = set()
        
        await server._deliver_notification(user_id, notification_data)
        
        mock_websocket.send.assert_called_once()
        assert len(server.pending_messages[user_id]) == 1

@pytest.mark.asyncio
async def test_cleanup_connection(websocket_server, user_id):
    async for server in websocket_server:
        server.connections[user_id] = mock.AsyncMock()
        server.pending_messages[user_id] = set()
        
        await server._cleanup_connection(user_id)
        
        assert user_id not in server.connections
        assert user_id not in server.pending_messages

@pytest.mark.asyncio
async def test_handle_status_update(websocket_server, user_id):
    async for server in websocket_server:
        message_id = uuid.uuid4()
        message = Message(
            type=MessageType.STATUS,
            payload={"status": "read"},
            user_id=user_id,
            message_id=message_id
        )
        server.pending_messages[user_id] = {message_id}
        
        await server._handle_status_update(message)
        
        assert message_id not in server.pending_messages[user_id]
        assert server.db_pool.acquire.called 