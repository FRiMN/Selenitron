import asyncio
from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional

import gevent
from arsenic import services, browsers, Session, get_session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver

import logger as logger_
from utils import get_chrome_options

# from gevent import monkey
# monkey.patch_socket()   # early as possible
if TYPE_CHECKING:
    from consumers import Consumer


logger = logger_.initLogging().getLogger(__name__)


@dataclass
class Task:
    width: int
    height: int
    data: Optional[bytes] = None

    def __str__(self):
        trunc_data = (self.data[:8] + b'..') if self.data and len(self.data) > 10 else self.data
        return f'Task(width={self.width}, height={self.height}, data={trunc_data})'


class BaseGenerator:
    tasks: List[Task]
    consumer: 'Consumer'

    def __init__(self, site_url: str, consumer: 'Consumer'):
        self.consumer = consumer
        self.site_url = site_url
        self.tasks = []

    def generate(self, height: int, width: int):
        raise NotImplementedError

    def add_task(self, width: int, height: int):
        task = Task(width=width, height=height)
        self.tasks.append(task)

    def _execute_task(self, task: Task) -> Task:
        task.data = self.generate(task.height, task.width)
        self.consumer.execute_task(task)
        return task

    def execute_tasks(self) -> List[Task]:
        raise NotImplementedError


class GeventGenerator(BaseGenerator):
    def execute_tasks(self) -> List[Task]:
        jobs = [gevent.spawn(self._execute_task, task) for task in self.tasks]
        gevent.joinall(jobs, timeout=5, raise_error=True)

        # By default, `gevent.joinall` don't raise exceptions from jobs.
        # We need to raise this by calling `Greenlet.get` for each job.
        [job.get() for job in jobs]

        # Return results from self._execute_task method for each job.
        return [job.value for job in jobs]


class AsyncGenerator(BaseGenerator):
    # loop: Optional[AbstractEventLoop] = None

    # def __init__(self, *args, **kwargs):
    #     self.loop = asyncio.get_event_loop()
    #     super().__init__(*args, **kwargs)

    @staticmethod
    def get_or_create_eventloop():
        try:
            return asyncio.get_event_loop()
        except RuntimeError as ex:
            if "There is no current event loop in thread" in str(ex):
                print('new event loop')
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return asyncio.get_event_loop()
            raise ex

    # async def _async_execute_tasks(self):
    #     pfuncs = [partial(self._execute_task, task) for task in self.tasks]
    #     jobs = [asyncio.create_task(pfunc) for pfunc in pfuncs]
    #     await asyncio.gather(jobs)

    async def _execute_task(self, task: Task) -> Task:
        print(f'**** async execute task {task}')
        task.data = await self.generate(task.height, task.width)
        self.consumer.execute_task(task)
        print(f'*-*-*-*-* complete task {task}')
        return task

    async def execute_tasks(self) -> List[Task]:
        futures = [self._execute_task(task) for task in self.tasks]
        print('futures', futures)
        # loop = self.get_or_create_eventloop()
        # loop.run_until_complete(asyncio.wait(futures))
        await asyncio.wait(futures)
        return self.tasks


class WebDriverGeneratorMixin:
    chrome_options: Options = get_chrome_options()
    webdriver_class = webdriver.Chrome

    def webdriver(self) -> WebDriver:
        """ Return instance of webdriver. Can use like context manager. """
        return self.webdriver_class(options=self.chrome_options)


class ArsenicGeneratorMixin:
    chrome_options: Options = get_chrome_options()
    service = services.Chromedriver()
    browser_cls = browsers.Chrome

    def session(self) -> Session:
        print('capabilities', self.chrome_options.capabilities)
        browser = self.browser_cls(**self.chrome_options.capabilities)
        return get_session(self.service, browser)
