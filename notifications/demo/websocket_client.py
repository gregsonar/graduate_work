import asyncio
import os
import sys
from datetime import datetime

import websockets
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# ID пользователя для демонстрации
USER_ID = "d6fa8c32-fdce-44cf-9444-9848119c36a3"

# URL WebSocket сервера
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8765")


async def connect_websocket():
    """Подключение к WebSocket серверу и получение сообщений."""
    while True:
        try:
            print(f"Попытка подключения к {WEBSOCKET_URL}")
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                print("Соединение установлено")

                # Отправляем ID пользователя для аутентификации
                print(f"Отправляем ID пользователя: {USER_ID}")
                await websocket.send(USER_ID)

                # Получаем подтверждение подключения
                response = await websocket.recv()
                if response == "OK":
                    print("Успешно подключились к серверу!")
                else:
                    print(f"Ошибка при подключении: {response}")
                    return

                print("\nОжидаем сообщения... (Для выхода нажмите Ctrl+C)\n")

                while True:
                    try:
                        message = await websocket.recv()
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{timestamp}] Получено сообщение: {message}")
                    except websockets.ConnectionClosed:
                        print("Соединение с сервером разорвано")
                        break

        except websockets.ConnectionClosed:
            print(f"Не удалось подключиться к {WEBSOCKET_URL}")
            print("Убедитесь, что сервер запущен и доступен")
            print("Повторная попытка через 5 секунд...")
            await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nЗавершение работы...")
            break
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Повторная попытка через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(connect_websocket())
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем")
        sys.exit(0)
