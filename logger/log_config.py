import logging

from settings import LOG_HANDLERS, LOGSTASH

logging_level = logging.DEBUG

CONFIG = dict(
    # See: <https://docs.python.org/3.7/library/logging.config.html#logging.config.fileConfig>
    # and find `disable_existing_loggers`, it's same configuration parameter as for dictConfig function.
    disable_existing_loggers=False,
    version=1,
    formatters={
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'logstash': {
            '()': 'logstash_formatter.LogstashFormatterV1'
        }
    },
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'level': logging_level,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'logstash': {
            'level': logging_level,
            'class': 'logstash.TCPLogstashHandler',
            'formatter': 'logstash',
            'host': LOGSTASH,
            'port': 5959,
        }
    },
    root={
        'handlers': LOG_HANDLERS,
        'level': logging_level,
    },
)
