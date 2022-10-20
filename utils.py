import logging
from functools import wraps
from time import time
from typing import Optional, List, Iterable
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from logger import initLogging

capabilities = webdriver.DesiredCapabilities.CHROME.copy()

logger = initLogging()

# Options description list:
# <https://peter.sh/experiments/chromium-command-line-switches/>
DEFAULT_CHROME_OPTIONS = [
    '--no-sandbox',     # has to be the very first option
    '--disable-dev-shm-usage',
    '--no-zygote',
    '--disable-features=TranslateUI',
    '--disable-extensions',
    '--disable-component-extensions-with-background-pages',
    '--disable-background-networking',
    '--disable-sync',
    '--metrics-recording-only',
    '--disable-default-apps',
    '--mute-audio',
    '--no-default-browser-check',
    '--no-first-run',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-background-timer-throttling',
    '--force-fieldtrials=*BackgroundTracing/default/',
    # '--remote-debugging-port=44333',
    '--disable-setuid-sandbox',
    # '--user-data-dir=/home/seluser/user-data',
    # '--profile-directory=Default',
    # '--remote-debugging-address=0.0.0.0',
]

LOGGERS_FOR_INJECT_EXTRA = (
    'botocore.hooks',
    'botocore.retryhandler',
    'botocore.parsers',
    'botocore.awsrequest',
    'crawler',
    'crawler.pipelines',
    'crawler.pipelines.pipeline_rabbitmq',
    'crawler.utils',
    'detectem',
    # 'docker',
    # 'docker.api',
    # 'docker.api.build',
    # 'docker.api.image',
    # 'docker.api.swarm',
    # 'docker.auth',
    # 'docker.utils',
    # 'docker.utils.config',
    # 'pika',
    # 'pika.adapters',
    # 'pika.adapters.base_connection',
    # 'pika.adapters.blocking_connection',
    # 'pika.adapters.select_connection',
    # 'pika.adapters.utils',
    # 'pika.adapters.utils.connection_workflow',
    # 'pika.adapters.utils.io_services_utils',
    # 'pika.adapters.utils.selector_ioloop_adapter',
    # 'pika.callback',
    # 'pika.channel',
    # 'pika.connection',
    # 'pika.credentials',
    # 'pika.frame',
    # 'pika.heartbeat',
    # 'pika.tcp_socket_opts',
    'py',
    'py.warnings',
    'pyasn1',
    'requests',
    'rotating_proxies',
    'rotating_proxies.expire',
    'rotating_proxies.middlewares',
    'scrapy',
    'scrapy.core',
    'scrapy.core.downloader',
    'scrapy.core.downloader.handlers',
    'scrapy.core.downloader.handlers.http11',
    'scrapy.core.downloader.tls',
    'scrapy.core.engine',
    'scrapy.core.scheduler',
    'scrapy.core.scraper',
    'scrapy.crawler',
    'scrapy.downloadermiddlewares',
    'scrapy.downloadermiddlewares.ajaxcrawl',
    'scrapy.downloadermiddlewares.cookies',
    'scrapy.downloadermiddlewares.redirect',
    'scrapy.downloadermiddlewares.retry',
    'scrapy.downloadermiddlewares.robotstxt',
    'scrapy.dupefilters',
    'scrapy.extensions',
    'scrapy.extensions.feedexport',
    'scrapy.extensions.httpcache',
    'scrapy.extensions.logstats',
    'scrapy.extensions.memusage',
    'scrapy.extensions.telnet',
    'scrapy.extensions.throttle',
    'scrapy.mail',
    'scrapy.middleware',
    'scrapy.pqueues',
    'scrapy.spidermiddlewares',
    'scrapy.spidermiddlewares.depth',
    'scrapy.spidermiddlewares.httperror',
    'scrapy.spidermiddlewares.offsite',
    'scrapy.spidermiddlewares.urllength',
    'scrapy.spiders',
    'scrapy.spiders.sitemap',
    'scrapy.statscollectors',
    'scrapy.utils',
    'scrapy.utils.iterators',
    'scrapy.utils.log',
    'scrapy.utils.signal',
    'scrapy.utils.spider',
    'scrapy_splash',
    'scrapy_splash.middleware',
    'sqlalchemy',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.mysql',
    'sqlalchemy.dialects.mysql.base',
    'sqlalchemy.dialects.mysql.base.MySQLDialect',
    'sqlalchemy.dialects.mysql.reflection',
    'sqlalchemy.dialects.mysql.reflection.MySQLTableDefinitionParser',
    'sqlalchemy.engine',
    'sqlalchemy.engine.base',
    'sqlalchemy.engine.base.Engine',
    'sqlalchemy.ext',
    'sqlalchemy.ext.baked',
    'sqlalchemy.orm',
    'sqlalchemy.orm.dynamic',
    'sqlalchemy.orm.dynamic.DynaLoader',
    'sqlalchemy.orm.mapper',
    'sqlalchemy.orm.mapper.Mapper',
    'sqlalchemy.orm.path_registry',
    'sqlalchemy.orm.properties',
    'sqlalchemy.orm.properties.ColumnProperty',
    'sqlalchemy.orm.query',
    'sqlalchemy.orm.query.Query',
    'sqlalchemy.orm.relationships',
    'sqlalchemy.orm.relationships.RelationshipProperty',
    'sqlalchemy.orm.strategies',
    'sqlalchemy.orm.strategies.ColumnLoader',
    'sqlalchemy.orm.strategies.DeferredColumnLoader',
    'sqlalchemy.orm.strategies.DoNothingLoader',
    'sqlalchemy.orm.strategies.ExpressionColumnLoader',
    'sqlalchemy.orm.strategies.JoinedLoader',
    'sqlalchemy.orm.strategies.LazyLoader',
    'sqlalchemy.orm.strategies.NoLoader',
    'sqlalchemy.orm.strategies.SelectInLoader',
    'sqlalchemy.orm.strategies.SubqueryLoader',
    'sqlalchemy.pool',
    'sqlalchemy.pool.impl',
    'sqlalchemy.pool.impl.QueuePool',
    'tldextract',
    'twisted',
    'urllib3',
    'urllib3.connection',
    'urllib3.connectionpool',
    'urllib3.contrib',
    'urllib3.contrib.pyopenssl',
    'urllib3.poolmanager',
    'urllib3.response',
    'urllib3.util',
    'urllib3.util.retry',
    'websocket',
    'asyncio',
    'backoff',
    'screenshoter.async_screenshoter',
    # 'worker',
    # 'root',
)


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        took = te - ts
        logger.debug(f'func:{f.__name__} args:[{args}, {kw}] took: {took:2.4f} sec')
        return result

    return wrap


def hide_scrollbars(driver: WebDriver):
    inject_css_hide_scrollbars = """
        const addStyle = (() => {
            const style = document.createElement('style');
            document.head.append(style);
            return (styleString) => style.textContent = styleString;
        })();

        const hide_scrollbars = `
            ::-webkit-scrollbar {
                display: none;
            }

            html > ::-webkit-scrollbar {
                width: 0px;
                display: none;
            }

            ::-webkit-scrollbar-thumb {
                display: none;
            }

            ::-webkit-scrollbar-track-piece {
                display: none;
            }
        `

        const callback = arguments[0];
        const handleDocumentLoaded = () => {
            addStyle(hide_scrollbars);
            callback();
        }

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", handleDocumentLoaded);
        } else {
            handleDocumentLoaded();
        }
    """
    driver.execute_async_script(inject_css_hide_scrollbars)


def add_partner_id_and_locale_in_url(url: str, partner_id: Optional[str] = None, locale: Optional[str] = None):
    scheme, netloc, path, query, fragment = urlsplit(url)
    parsed_query = parse_qsl(query)
    if partner_id:
        parsed_query.append(('partner_id', partner_id))
    if locale:
        parsed_query.append(('locale', locale))
    query = urlencode(parsed_query)
    url = urlunsplit((scheme, netloc, path, query, fragment))
    return url


def get_chrome_options(arguments: List[str] = None) -> Options:
    if arguments is None:
        arguments = []
    options = webdriver.ChromeOptions()

    arguments += DEFAULT_CHROME_OPTIONS
    for arg in arguments:
        options.add_argument(arg)

    options.headless = True
    return options


class ExtraFilter(logging.Filter):
    """ Filter to add additional fields to the logger """

    def __init__(self, key, value, *args, **kwargs):
        super(ExtraFilter, self).__init__(*args, **kwargs)
        self.key = key
        self.value = value

    def filter(self, record):
        if self.value:
            # From logging.Logger.makeRecord
            if hasattr(record, self.key) or (self.key in ["message", "asctime"]):
                raise KeyError("Attempt to overwrite %r in LogRecord" % self.key)

            setattr(record, self.key, self.value)
        return True


def inject_fields_in_logger(extra: dict, loggers: Iterable = LOGGERS_FOR_INJECT_EXTRA):
    """ Injecting extra fields to each logger in loggers """
    filters_for_inject_extra = [ExtraFilter(k, v) for k, v in extra.items()]
    reject_fields_from_logger(extra, loggers)
    for logger in loggers:
        if isinstance(logger, str):
            logger = logging.getLogger(logger)
        for inject_filter in filters_for_inject_extra:
            logger.addFilter(inject_filter)


def reject_fields_from_logger(extra: dict, loggers: Iterable = LOGGERS_FOR_INJECT_EXTRA):
    """ Rejecting extra fields from each logger in loggers """
    filters_for_inject_extra = [ExtraFilter(k, v) for k, v in extra.items()]
    for logger in loggers:
        if isinstance(logger, str):
            logger = logging.getLogger(logger)
        for inject_filter in filters_for_inject_extra:
            for exist_filter in logger.filters:
                if isinstance(exist_filter, ExtraFilter) and exist_filter.key == inject_filter.key:
                    logger.removeFilter(exist_filter)
