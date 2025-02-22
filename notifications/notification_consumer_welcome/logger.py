import logging
from logging.handlers import RotatingFileHandler
import os

import logstash


logger = logging.getLogger("notification_consumer_welcome_app")
logger.setLevel(logging.INFO)

fh = RotatingFileHandler("logs/consumer.log", maxBytes=20000000, backupCount=5)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)-8s [%(filename)-16s:%(lineno)-5d] %(message)s"
)
fh.setFormatter(formatter)
logger.addHandler(fh)

logstash_host = os.getenv("LOGSTASH_HOST", "logstash")
logstash_port = os.getenv("LOGSTASH_PORT", 5044)
logger.addHandler(
    logstash.LogstashHandler(logstash_host, int(logstash_port), version=1)
)
logger = logging.LoggerAdapter(
    logger, extra={"tag": "notification_consumer_welcome_app"}
)
