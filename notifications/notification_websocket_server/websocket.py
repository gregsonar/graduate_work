import asyncio
import os
import uuid

import aio_pika
import asyncpg
from typing import Dict, Optional
import websockets

from settings.extensions import logger
from settings.config import (
    RABBIT_HOST,
    RABBIT_USER,
    RABBIT_PASS,
    RABBIT_USER_INSTANT_MESSAGE_QUEUE,
    MESSAGES_DSL,
)


USERS: Dict[uuid.UUID, websockets.WebSocketServerProtocol] = {}


class WrongUserCredentials(BaseException):
    def __init__(self, e):
        super(WrongUserCredentials, self).__init__()
        self._e = e

    def __str__(self):
        return f'Cannot recognise user credentials. detail: {self._e}'


async def connect(websocket: websockets.WebSocketServerProtocol) -> uuid.UUID:
    try:
        data = await websocket.recv()
        user_id = uuid.UUID(data.replace('\n', ''))
    except ValueError as e:
        logger.error('Wrong uuid format for user id %s', data)
        raise WrongUserCredentials(e)

    USERS[user_id] = websocket
    await websocket.send('OK')
    return user_id


async def receiver(
    websocket: websockets.WebSocketServerProtocol, path: str
) -> None:
    user_id: Optional[uuid.UUID] = None
    try:
        user_id = await connect(websocket)
        await handle_user_messages(user_id)
    except WrongUserCredentials as e:
        await websocket.send(str(e))
    finally:
        await unregister(user_id)
        await websocket.send('Connection closed.')


async def handle_user_messages(user_id: uuid.UUID):

    connection = await aio_pika.connect_robust(
        f'amqp://{RABBIT_USER}:{RABBIT_PASS}@{RABBIT_HOST}/', loop=loop
    )

    user_queue = f'{RABBIT_USER_INSTANT_MESSAGE_QUEUE}.{user_id}'

    async for message in rabbit_messages(connection, user_queue):
        text_message = message.body
        await proceed_websocket_message(user_id, text_message)


async def rabbit_messages(connection: aio_pika.connection, queue: str):
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    yield message


async def proceed_websocket_message(user_id: uuid.UUID, text_message: str):
    websocket = USERS.get(user_id)
    await websocket.send(text_message)
    await save_to_db(user_id, text_message)
    await asyncio.sleep(1)


async def save_to_db(user_id: uuid.UUID, message: str) -> None:
    with await asyncpg.connect(**MESSAGES_DSL) as conn:
        query = f'INSERT INTO notification_messages (id, user_id, message) VALUES (%s, %s, %s)'
        await conn.execute(query, (str(uuid.uuid4()), str(user_id), message))


async def unregister(user_id: Optional[uuid.UUID]):
    if user_id is None:
        return
    _ = USERS.pop(user_id)


ws_server = websockets.serve(receiver, '0.0.0.0', 8765)

loop = asyncio.get_event_loop()
loop.run_until_complete(ws_server)
loop.run_forever()
