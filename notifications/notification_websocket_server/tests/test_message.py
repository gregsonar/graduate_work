import json
import uuid
import pytest
from notifications.notification_websocket_server.websocket import Message, MessageType

@pytest.fixture
def user_id():
    return uuid.uuid4()

@pytest.fixture
def message_id():
    return uuid.uuid4()

def test_message_to_json(user_id, message_id):
    message = Message(
        type=MessageType.NOTIFICATION,
        payload={"content": "test message"},
        user_id=user_id,
        message_id=message_id
    )
    
    json_str = message.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["type"] == MessageType.NOTIFICATION.value
    assert parsed["payload"] == {"content": "test message"}
    assert parsed["message_id"] == str(message_id)

def test_message_from_json(user_id):
    data = {
        "type": "notification",
        "payload": {"content": "test message"},
        "message_id": str(uuid.uuid4())
    }
    
    message = Message.from_json(json.dumps(data), user_id)
    
    assert message.type == MessageType.NOTIFICATION
    assert message.payload == {"content": "test message"}
    assert message.user_id == user_id
    assert isinstance(message.message_id, uuid.UUID)

def test_message_from_json_without_message_id(user_id):
    data = {
        "type": "status",
        "payload": {"status": "read"}
    }
    
    message = Message.from_json(json.dumps(data), user_id)
    
    assert message.type == MessageType.STATUS
    assert message.payload == {"status": "read"}
    assert message.user_id == user_id
    assert isinstance(message.message_id, uuid.UUID)

def test_message_from_json_invalid_type(user_id):
    data = {
        "type": "invalid_type",
        "payload": {}
    }
    
    with pytest.raises(ValueError):
        Message.from_json(json.dumps(data), user_id)

def test_message_from_json_invalid_json(user_id):
    with pytest.raises(json.JSONDecodeError):
        Message.from_json("invalid json", user_id) 