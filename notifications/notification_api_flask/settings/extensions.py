import logstash
import os

import logging

from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData


naming_convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(column_0_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
ma = Marshmallow()


logger = logging.getLogger('Auth app logger')
logger.setLevel(logging.INFO)
logstash_host = os.getenv('LOGSTASH_HOST', 'logstash')
logstash_port = os.getenv('LOGSTASH_PORT', 5044)


logger.addHandler(
    logstash.LogstashHandler(logstash_host, int(logstash_port), version=1)
)
logger.addHandler(logging.StreamHandler())
logger = logging.LoggerAdapter(logger, extra={'tag': 'notification_api_app'})
