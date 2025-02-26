from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from yookassa.domain.exceptions import ApiError
from yookassa.domain.notification import WebhookNotification

from payments.webhook_app import app

client = TestClient(app)


@pytest.fixture
def mock_yookassa_provider():
    with patch("payments.webhook_app.provider") as mock_provider:
        yield mock_provider


@pytest.mark.asyncio
async def test_yookassa_webhook_payment_succeeded(mock_yookassa_provider):
    event_json = {
        "event": "payment.succeeded",
        "object": {"id": "payment_id_123", "status": "succeeded"},
    }
    mock_notification = MagicMock(spec=WebhookNotification)
    mock_notification.object = event_json["object"]
    mock_notification.event = event_json["event"]

    with patch(
        "yookassa.domain.notification.WebhookNotification",
        return_value=mock_notification,
    ):
        response = client.post("/webhook/yookassa", json=event_json)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_yookassa_webhook_payment_waiting_for_capture(mock_yookassa_provider):
    event_json = {
        "event": "payment.waiting_for_capture",
        "object": {"id": "payment_id_123", "status": "waiting_for_capture"},
    }
    mock_notification = MagicMock(spec=WebhookNotification)
    mock_notification.object = event_json["object"]
    mock_notification.event = event_json["event"]

    with patch(
        "yookassa.domain.notification.WebhookNotification",
        return_value=mock_notification,
    ):
        response = client.post("/webhook/yookassa", json=event_json)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_yookassa_provider.capture_payment.assert_called_once_with("payment_id_123")


@pytest.mark.asyncio
async def test_yookassa_webhook_payment_canceled(mock_yookassa_provider):
    event_json = {
        "event": "payment.canceled",
        "object": {"id": "payment_id_123", "status": "canceled"},
    }
    mock_notification = MagicMock(spec=WebhookNotification)
    mock_notification.object = event_json["object"]
    mock_notification.event = event_json["event"]

    with patch(
        "yookassa.domain.notification.WebhookNotification",
        return_value=mock_notification,
    ):
        response = client.post("/webhook/yookassa", json=event_json)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_yookassa_webhook_api_error(mock_yookassa_provider):
    event_json = {
        "event": "payment.waiting_for_capture",
        "object": {"id": "payment_id_123", "status": "waiting_for_capture"},
    }
    mock_notification = MagicMock(spec=WebhookNotification)
    mock_notification.object = event_json["object"]
    mock_notification.event = event_json["event"]

    with patch(
        "yookassa.domain.notification.WebhookNotification",
        return_value=mock_notification,
    ), patch(
        "payments.webhook_app.provider.capture_payment",
        side_effect=ApiError("API Error"),
    ):
        response = client.post("/webhook/yookassa", json=event_json)
        assert response.status_code == 400
        assert response.json()["detail"] == "Ошибка API: API Error"


@pytest.mark.asyncio
async def test_yookassa_webhook_general_error(mock_yookassa_provider):
    event_json = {
        "event": "payment.waiting_for_capture",
        "object": {"id": "payment_id_123", "status": "waiting_for_capture"},
    }
    mock_notification = MagicMock(spec=WebhookNotification)
    mock_notification.object = event_json["object"]
    mock_notification.event = event_json["event"]

    with patch(
        "yookassa.domain.notification.WebhookNotification",
        return_value=mock_notification,
    ), patch(
        "payments.webhook_app.provider.capture_payment",
        side_effect=Exception("General Error"),
    ):
        response = client.post("/webhook/yookassa", json=event_json)
        assert response.status_code == 400
        assert response.json()["detail"] == "Ошибка обработки вебхука: General Error"
