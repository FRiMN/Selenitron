import logging
from logging.config import dictConfig

from logger.log_config import CONFIG


def initLogging():
    dictConfig(CONFIG)
    return logging
