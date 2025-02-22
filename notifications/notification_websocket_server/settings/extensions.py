import os
import logging
import sys

from logstash_async.handler import AsynchronousLogstashHandler


logstash_host = os.getenv("LOGSTASH_HOST", "logstash")
logstash_port = int(os.getenv("LOGSTASH_PORT", 5044))

logger = logging.getLogger("websocket-server-logger")
logger.setLevel(logging.INFO)

# Добавляем обработчик для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Добавляем обработчик для Logstash
logger.addHandler(AsynchronousLogstashHandler(logstash_host, logstash_port, None))
