import os
import logging

from logstash_async.handler import AsynchronousLogstashHandler


logstash_host = os.getenv("LOGSTASH_HOST", "logstash")
logstash_port = os.getenv("LOGSTASH_PORT", 5044)

logger = logging.getLogger("websocket-server-logger")
logger.setLevel(logging.INFO)
logger.addHandler(AsynchronousLogstashHandler(logstash_host, logstash_port, None))
