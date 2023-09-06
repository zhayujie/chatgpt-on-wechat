# -*- coding: utf-8 -*-
"""
@Time ： 2023/9/5 14:51
@Auth ： HuangChenjian
@File ：google_fns.py
@IDE ：PyCharm
"""

import requests

from bs4 import BeautifulSoup

from .util import  input_clipping


def bing_search(query, proxies=None):
    query = query
    url = f"https://cn.bing.com/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'}
    response = requests.get(url, headers=headers, proxies=proxies)
    soup = BeautifulSoup(response.content, 'html.parser')
    results = []
    for g in soup.find_all('li', class_='b_algo'):
        anchors = g.find_all('a')
        if anchors:
            link = anchors[0]['href']
            if not link.startswith('http'):
                continue
            title = g.find('h2').text
            item = {'title': title, 'link': link}
            results.append(item)

    for r in results:
        print(r['link'])
    return results
def google(query, proxies):
    query = query # 在此处替换您要搜索的关键词
    url = f"https://www.google.com/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'}
    response = requests.get(url, headers=headers, proxies=proxies)
    soup = BeautifulSoup(response.content, 'html.parser')
    results = []
    for g in soup.find_all('div', class_='g'):
        anchors = g.find_all('a')
        if anchors:
            link = anchors[0]['href']
            if link.startswith('/url?q='):
                link = link[7:]
            if not link.startswith('http'):
                continue
            title = g.find('h3').text
            item = {'title': title, 'link': link}
            results.append(item)

    for r in results:
        print(r['link'])
    return results

def scrape_text(url, proxies) -> str:
    """Scrape text from a webpage

    Args:
        url (str): The URL to scrape text from

    Returns:
        str: The scraped text
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
        'Content-Type': 'text/plain',
    }
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=8)
        if response.encoding == "ISO-8859-1": response.encoding = response.apparent_encoding
    except:
        return "无法连接到该网页"
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return text

def search_by_google(txt):
    urls = google(txt, proxies)
    history = []
    chatbot = []
    max_search_result = 5  # 最多收纳多少个网页的结果
    for index, url in enumerate(urls[:max_search_result]):
        res = scrape_text(url['link'], proxies)
        history.extend([f"第{index}份搜索结果：", res])
        chatbot.append([f"第{index}份搜索结果：", res[:500] + "......"])
        # print(f"第{index}份搜索结果：", res[:500] + "......")
    i_say = f"从以上搜索结果中抽取信息，然后回答问题：{txt}"
    i_say, history = input_clipping(  # 裁剪输入，从最长的条目开始裁剪，防止爆token
        inputs=i_say,
        history=history,
        max_token_limit=4096 * 3 // 4
    )
    return history

proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
if __name__ == '__main__':
    pass
