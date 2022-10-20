import io
from time import sleep
from typing import Optional

from PIL import Image
from arsenic.session import Session
from selenium.webdriver.chrome.webdriver import WebDriver

from generators import GeventGenerator, WebDriverGeneratorMixin, AsyncGenerator, BaseGenerator, ArsenicGeneratorMixin
from logger import initLogging
from utils import get_chrome_options, hide_scrollbars

logger = initLogging().getLogger(__name__)


class BaseScreenshotGenerator(BaseGenerator):
    chrome_options = get_chrome_options([
        '--high-dpi-support=1',
        '--hide-scrollbars'
    ])

    def get_screenshot(self, driver) -> io.BytesIO:
        raise NotImplementedError

    def get_clrs(self, image: io.BytesIO) -> list[tuple[int, int]]:
        with Image.open(image) as image:
            return image.getcolors(1000000)

    def is_blank(self, image: io.BytesIO) -> bool:
        """ detect blank image (full white) """
        return len(self.get_clrs(image)) < 3

    def is_change(self, image: io.BytesIO, prev_clrs: list[tuple]) -> bool:
        """ image changed """
        return len(self.get_clrs(image)) != len(prev_clrs)

    def get_last_screenshot(self, driver, attempt=1, prev_clrs: Optional[list[tuple]] = None) -> io.BytesIO:
        """ Recursive takes screenshots until one of them matches """
        screenshot = self.get_screenshot(driver)
        prev_clrs = prev_clrs or []

        if attempt < 20 and (self.is_blank(screenshot) or self.is_change(screenshot, prev_clrs)):
            sleep(0.5)
            return self.get_last_screenshot(driver, attempt=attempt + 1, prev_clrs=self.get_clrs(screenshot))

        return screenshot

    def convert_to_jpeg(self, im: io.BytesIO) -> bytes:
        with Image.open(im) as im:
            im = im.convert('RGB')  # avoid transparency from png
            with io.BytesIO() as f:
                im.save(f, format='jpeg', quality=60)
                return f.getvalue()


class ScreenshotGenerator(BaseScreenshotGenerator, GeventGenerator, WebDriverGeneratorMixin):
    def get_screenshot(self, driver: WebDriver) -> io.BytesIO:
        image_bytes = driver.get_screenshot_as_png()
        return io.BytesIO(image_bytes)

    def generate(self, height: int, width: int) -> bytes:
        logger.debug('get_image start')

        with self.webdriver() as driver:
            # set viewport as request image size
            width += 10  # side bar
            height += 82  # top bar
            driver.set_window_size(width, height)

            driver.execute_cdp_cmd('Animation.setPlaybackRate', {'playbackRate': 10000})
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': width, 'height': height,
                'mobile': True, 'deviceScaleFactor': 1, 'fitWindow': False,
                'screenWidth': width, 'screenHeight': height
            })

            driver.get(self.site_url)
            hide_scrollbars(driver)

            image = self.get_last_screenshot(driver)
        image = self.convert_to_jpeg(image)
        logger.debug('get_image stop')
        return image


class AsyncScreenshotGenerator(BaseScreenshotGenerator, AsyncGenerator, ArsenicGeneratorMixin):
    async def get_screenshot(self, driver: Session) -> io.BytesIO:
        print('get screenshot')
        s = await driver.get_screenshot()
        print('--==>', s)
        return s

    async def get_last_screenshot(self, driver, attempt=1, prev_clrs: Optional[list[tuple]] = None) -> io.BytesIO:
        """ Recursive takes screenshots until one of them matches """
        screenshot = await self.get_screenshot(driver)
        print('===>', screenshot)
        prev_clrs = prev_clrs or []

        if attempt < 20 and (self.is_blank(screenshot) or self.is_change(screenshot, prev_clrs)):
            sleep(0.5)
            return await self.get_last_screenshot(driver, attempt=attempt + 1, prev_clrs=self.get_clrs(screenshot))

        return screenshot

    async def generate(self, height: int, width: int) -> bytes:
        async with self.session() as session:
            # set viewport as request image size
            width += 10  # side bar
            height += 82  # top bar
            await session.set_window_size(width, height)

            # session.execute_cdp_cmd('Animation.setPlaybackRate', {'playbackRate': 10000})
            # session.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            #     'width': width, 'height': height,
            #     'mobile': True, 'deviceScaleFactor': 1, 'fitWindow': False,
            #     'screenWidth': width, 'screenHeight': height
            # })

            await session.get(self.site_url)
            # hide_scrollbars(session)

            image = await self.get_last_screenshot(session)
        image = self.convert_to_jpeg(image)
        logger.debug('get_image stop')
        return image
        # return b''
