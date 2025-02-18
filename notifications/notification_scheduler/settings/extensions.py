import logstash
import os

import logging


logger = logging.getLogger("Auth app logger")
logger.setLevel(logging.INFO)
logstash_host = os.getenv("LOGSTASH_HOST", "logstash")
logstash_port = os.getenv("LOGSTASH_PORT", 5044)

logger.addHandler(
    logstash.LogstashHandler(logstash_host, int(logstash_port), version=1)
)
logger.addHandler(logging.StreamHandler())
logger = logging.LoggerAdapter(logger, extra={"tag": "notification_scheduler"})
