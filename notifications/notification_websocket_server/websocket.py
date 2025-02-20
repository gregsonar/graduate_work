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
        logger.info('Waiting for user ID from WebSocket connection...')
        data = await websocket.recv()
        user_id = uuid.UUID(data.replace('\n', ''))
        logger.info(f'Received user ID: {user_id}')
    except ValueError as e:
        logger.error('Wrong uuid format for user id %s', data)
        raise WrongUserCredentials(e)

    USERS[user_id] = websocket
    logger.info(f'User {user_id} connected successfully')
    await websocket.send('OK')
    return user_id


async def receiver(
    websocket: websockets.WebSocketServerProtocol, path: str
) -> None:
    user_id: Optional[uuid.UUID] = None
    try:
        logger.info('New WebSocket connection received')
        user_id = await connect(websocket)
        await handle_user_messages(user_id)
    except WrongUserCredentials as e:
        logger.error(f'Authentication failed: {e}')
        await websocket.send(str(e))
    except Exception as e:
        logger.error(f'Unexpected error in receiver: {e}')
    finally:
        await unregister(user_id)
        logger.info(f'Connection closed for user {user_id}')
        await websocket.send('Connection closed.')


async def handle_user_messages(user_id: uuid.UUID):
    logger.info(f'Starting message handling for user {user_id}')
    try:
        connection = await aio_pika.connect_robust(
            f'amqp://{RABBIT_USER}:{RABBIT_PASS}@{RABBIT_HOST}/'
        )
        logger.info('Successfully connected to RabbitMQ')

        user_queue = f'{RABBIT_USER_INSTANT_MESSAGE_QUEUE}.{user_id}'
        logger.info(f'Using queue: {user_queue}')

        async for message in rabbit_messages(connection, user_queue):
            text_message = message.body.decode('utf-8')
            logger.info(f'Received message for user {user_id}: {text_message}')
            await proceed_websocket_message(user_id, text_message)
    except Exception as e:
        logger.error(f'Error in handle_user_messages: {e}')
        raise


async def rabbit_messages(connection: aio_pika.connection, queue: str):
    try:
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(queue, durable=True)
            logger.info(f'Successfully declared queue: {queue.name}')

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        yield message
    except Exception as e:
        logger.error(f'Error in rabbit_messages: {e}')
        raise


async def proceed_websocket_message(user_id: uuid.UUID, text_message: str):
    try:
        websocket = USERS.get(user_id)
        if websocket:
            await websocket.send(text_message)
            logger.info(f'Sent message to user {user_id}')
            await save_to_db(user_id, text_message)
        else:
            logger.warning(f'User {user_id} not found in active connections')
    except Exception as e:
        logger.error(f'Error in proceed_websocket_message: {e}')
        raise


async def save_to_db(user_id: uuid.UUID, message: str) -> None:
    try:
        async with asyncpg.connect(**MESSAGES_DSL) as conn:
            query = 'INSERT INTO notification_messages (id, user_id, message) VALUES ($1, $2, $3)'
            message_id = str(uuid.uuid4())
            await conn.execute(query, message_id, str(user_id), message)
            logger.info(f'Saved message {message_id} for user {user_id} to database')
    except Exception as e:
        logger.error(f'Error saving message to database: {e}')
        raise


async def unregister(user_id: Optional[uuid.UUID]):
    if user_id is None:
        return
    try:
        _ = USERS.pop(user_id)
        logger.info(f'Unregistered user {user_id}')
    except KeyError:
        logger.warning(f'User {user_id} not found during unregistration')


async def main():
    logger.info('Starting WebSocket server...')
    try:
        async with websockets.serve(receiver, '0.0.0.0', 8765):
            logger.info('WebSocket server is running on ws://0.0.0.0:8765')
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.error(f'Error starting WebSocket server: {e}')
        raise


if __name__ == "__main__":
    try:
        logger.info('Initializing WebSocket application')
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Shutting down WebSocket server...')
    except Exception as e:
        logger.error(f'Fatal error: {e}')
