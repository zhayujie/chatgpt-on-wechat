from playwright.sync_api import sync_playwright
from common.log import logger

class WebScraper:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

    def get_content(self, url):
        try:
            page = self.browser.new_page()
            page.goto(url)
            
            # 提取标题和正文内容
            title = page.title()
            body = page.query_selector('body').inner_text()  # 根据实际的选择器调整
            
            content = title + '\n' + body
            page.close()
            return content
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return ""

    def close(self):
        self.browser.close()
        self.playwright.stop()

if __name__ == '__main__':
    scraper = WebScraper()
    content = scraper.get_content('https://mp.weixin.qq.com/s/OC71o5puU9nIkng3U6Fm4w')
    print(content)
    scraper.close()