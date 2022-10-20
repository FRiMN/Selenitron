import time
from functools import wraps
from urllib.parse import urlparse, urlunparse

import requests
from requests.exceptions import ConnectionError

import logger

TIMES_TO_TRY = 3
RETRY_DELAY = 5


def retry(ExceptionToCheck, tries=TIMES_TO_TRY, delay=RETRY_DELAY, log=None):
    """Retry calling the decorated function.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    :param ExceptionToCheck: Exception or tuple to check
    :param tries: int number of times to try (not retry) before giving up
    :param delay: int initial delay between retries in seconds
    :param log: logger instance
    """

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries = tries
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    log.warning("Connection error {}, retying {}, delay {}".format(
                        ExceptionToCheck.__name__, tries, delay))
                    time.sleep(delay)
                    mtries -= 1
            try:
                return f(*args, **kwargs)
            except ExceptionToCheck as e:
                log.error('Fatal Error: %s' % e)
                exit(1)

        return f_retry

    return deco_retry


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseRemoteService(metaclass=Singleton):

    session = None

    def __init__(self, url_prefix: str):
        self.url_prefix = url_prefix
        self.session = SmartSession(session=requests.Session(), url_prefix=url_prefix)

class SmartSession:
    """
    A smart session class.
    """

    logger = logger.initLogging()

    def __init__(self, session: requests.Session, url_prefix: str):
        self.session = session
        self.url_prefix = url_prefix
        self.authentificate()

    def __getattr__(self, func_name: str):
        """
        Use the magic method to forward all RESTful function calls to the inner requests session object.
        :param func_name: a dynamic function name that the requests session accepts, such as get, post, put, delete
        :return: a function method object
        """
        @retry(ConnectionError, log=self.logger)
        def method(*args, **kwargs):
            # get the dynamic function object from the requests session object

            func = getattr(self.session, func_name)

            # no auto redirect so we can get status code 302 instead of 200 when the cookie expires
            kwargs['allow_redirects'] = False

            # Temporary fix for ConnectionResetError till urllib patched
            try:
                resp = func(*args, **kwargs)
            except:
                self.session = requests.Session()
                self.authentificate()
                func = getattr(self.session, func_name)
                resp = func(*args, **kwargs)

            return resp

        return method

    def authentificate(self):
        # Check for basic authentication
        parsed_url = urlparse(self.url_prefix)
        if parsed_url.username and parsed_url.password:
            netloc = parsed_url.hostname
            if parsed_url.port:
                netloc += ":%d" % parsed_url.port

            # remove username and password from the base_url
            self.url_prefix = urlunparse(
                (parsed_url.scheme, netloc, parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
            # configure requests to use basic auth
            self.session.auth = (parsed_url.username, parsed_url.password)
