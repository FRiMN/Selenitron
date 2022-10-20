import base64

from generators import GeventGenerator, WebDriverGeneratorMixin


class PdfGenerator(GeventGenerator, WebDriverGeneratorMixin):
    def generate(self, width: int, height: int):
        with self.webdriver() as driver:
            driver.execute_cdp_cmd('Animation.setPlaybackRate', {'playbackRate': 10000})
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': width, 'height': height,
                'mobile': True, 'deviceScaleFactor': 1, 'fitWindow': False,
                'screenWidth': width, 'screenHeight': height
            })

            driver.get(self.site_url)

            print_options = {
                'landscape': False,
                'displayHeaderFooter': False,
                'printBackground': True,
                'preferCSSPageSize': True,
            }
            result = driver.execute_cdp_cmd("Page.printToPDF", print_options)

        pdf = base64.b64decode(result['data'])
        return pdf
