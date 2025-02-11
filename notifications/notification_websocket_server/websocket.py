import asyncio
import json
import uuid
from pprint import pprint
from typing import Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

import aio_pika
import asyncpg
import websockets
from websockets.exceptions import ConnectionClosed

from notifications.notification_websocket_server.settings.config import (
    RABBIT_HOST,
    RABBIT_USER,
    RABBIT_PASS,
    RABBIT_USER_INSTANT_MESSAGE_QUEUE,
    MESSAGES_DSL,
)
from notifications.notification_websocket_server.settings.extensions import logger


class MessageType(Enum):
    NOTIFICATION = "notification"
    STATUS = "status"
    SYSTEM = "system"


@dataclass
class Message:
    type: MessageType
    payload: dict
    user_id: uuid.UUID
    message_id: uuid.UUID = None

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "payload": self.payload,
            "message_id": str(self.message_id or uuid.uuid4())
        })

    @classmethod
    def from_json(cls, data: str, user_id: uuid.UUID):
        parsed = json.loads(data)
        return cls(
            type=MessageType(parsed["type"]),
            payload=parsed["payload"],
            user_id=user_id,
            message_id=uuid.UUID(parsed.get("message_id", str(uuid.uuid4())))
        )


class WebSocketServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.connections: Dict[uuid.UUID, websockets.ServerProtocol] = {}
        self.pending_messages: Dict[uuid.UUID, Set[uuid.UUID]] = {}
        self.rabbit_connection = None
        self.db_pool = None

    async def initialize(self):
        # self.rabbit_connection = await aio_pika.connect_robust(
        #     f'amqp://{RABBIT_USER}:{RABBIT_PASS}@{RABBIT_HOST}/'
        # )
        self.rabbit_connection = await aio_pika.connect_robust(
            f'amqp://rabbit:rabbit@localhost/'
        )
        pprint(MESSAGES_DSL)
        self.db_pool = await asyncpg.create_pool(**MESSAGES_DSL)

    async def handle_client(self, websocket: websockets.ServerProtocol, path: str):
        user_id = None
        try:
            user_id = await self._authenticate_client(websocket)
            self.connections[user_id] = websocket
            self.pending_messages[user_id] = set()

            await asyncio.gather(
                self._handle_client_messages(websocket, user_id),
                self._handle_notifications(user_id)
            )
        except Exception as e:
            logger.error(f"Error handling client: {str(e)}")
        finally:
            await self._cleanup_connection(user_id)

    async def _authenticate_client(self, websocket: websockets.ServerProtocol) -> uuid.UUID:
        try:
            data = await websocket.recv()
            user_id = uuid.UUID(data.strip())
            await websocket.send(json.dumps({"status": "connected"}))
            return user_id
        except ValueError as e:
            raise ValueError(f"Invalid authentication data: {str(e)}")

    async def _handle_client_messages(self, websocket: websockets.ServerProtocol, user_id: uuid.UUID):
        try:
            async for message in websocket:
                try:
                    msg = Message.from_json(message, user_id)
                    if msg.type == MessageType.STATUS:
                        await self._handle_status_update(msg)
                except json.JSONDecodeError:
                    logger.error(f"Invalid message format from user {user_id}")
        except ConnectionClosed:
            logger.info(f"Client {user_id} connection closed")

    async def _handle_notifications(self, user_id: uuid.UUID):
        channel = await self.rabbit_connection.channel()
        queue_name = f"{RABBIT_USER_INSTANT_MESSAGE_QUEUE}.{user_id}"
        queue = await channel.declare_queue(queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self._deliver_notification(user_id, message.body)

    async def _deliver_notification(self, user_id: uuid.UUID, notification_data: bytes):
        websocket = self.connections.get(user_id)
        if not websocket:
            return

        try:
            message = Message(
                type=MessageType.NOTIFICATION,
                payload=json.loads(notification_data),
                user_id=user_id
            )
            await websocket.send(message.to_json())
            self.pending_messages[user_id].add(message.message_id)
            await self._save_notification(message)
        except Exception as e:
            logger.error(f"Error delivering notification: {str(e)}")

    async def _handle_status_update(self, message: Message):
        if message.message_id in self.pending_messages[message.user_id]:
            self.pending_messages[message.user_id].remove(message.message_id)
            await self._update_notification_status(message)

    async def _save_notification(self, message: Message):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO notification_messages (id, user_id, message, status)
                VALUES ($1, $2, $3, 'sent')
                """,
                str(message.message_id),
                str(message.user_id),
                json.dumps(message.payload)
            )

    async def _update_notification_status(self, message: Message):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE notification_messages
                SET status = $1, updated_at = NOW()
                WHERE id = $2
                """,
                message.payload.get("status", "delivered"),
                str(message.message_id)
            )

    async def _cleanup_connection(self, user_id: Optional[uuid.UUID]):
        if user_id:
            self.connections.pop(user_id, None)
            self.pending_messages.pop(user_id, None)

    async def start(self):
        await self.initialize()
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # run forever


if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.run(server.start())