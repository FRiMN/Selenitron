from unittest import mock

import pytest
from selenium.common.exceptions import WebDriverException

from consumers import StreamConsumer
from generators.screenshot import ScreenshotGenerator


def test_quit_on_exception():
    """ Test quit from selenium webdriver (close crashed tab) if raises exception on loading webpage """
    c = StreamConsumer()
    g = ScreenshotGenerator('http://example.org', c)
    g.add_task(0, 0)

    with mock.patch.object(g.webdriver_class, 'get', side_effect=WebDriverException()) as mocked_get, \
            mock.patch.object(g.webdriver_class, 'quit') as mocked_quit:

        with pytest.raises(WebDriverException):
            g.execute_tasks()

        assert mocked_get.call_count == 1
        assert mocked_quit.call_count == 1
