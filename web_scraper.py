# 文件名：web_scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from common.log import logger

class WebScraper:
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=options)

    def get_content(self, url):
        try:
            self.driver.get(url)
            content = self.driver.find_element(By.TAG_NAME, 'body').text
            return content
        except Exception as e:
            logger.error(e)
            return ""
        finally:
            self.driver.quit()