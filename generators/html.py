from generators import GeventGenerator, WebDriverGeneratorMixin


class HTMLGenerator(GeventGenerator, WebDriverGeneratorMixin):
    def generate(self, width: int, height: int):
        with self.webdriver() as driver:
            driver.get(self.site_url)

            # Executed on the page after the page has loaded. Strips script and
            # import tags to prevent further loading of resources.
            driver.execute_script('''
                const elements = document.querySelectorAll('script, link[rel=import]');
                elements.forEach((e) => e.remove());
            ''')

            # Fix links on page:
            # injects a <base> tag which allows other resources to load.
            driver.execute_script(f'''
                const base = document.createElement('base');
                base.setAttribute('href', '{self.site_url}');
                document.head.appendChild(base);
            ''')

            # Get content of page (HTML tag)
            content = driver.find_element_by_xpath('//html').get_attribute('outerHTML')

        return content
