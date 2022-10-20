from time import time

from gevent import sleep

from consumers import StreamConsumer
from generators import GeventGenerator


class DumbGenerator(GeventGenerator):
    counter = 0

    def generate(self, height: int, width: int):
        self.counter += 1
        # with Timeout(5):
        sleep(5*2)
        print(f'Count: {self.counter}; {time()}')


def test_gevent_fail():
    c = StreamConsumer()
    g = DumbGenerator('http://example.org', c)

    while True:
        g.add_task(0, 0)
        g.execute_tasks()
