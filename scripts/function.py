import json
import urllib.parse
import urllib.request
import urllib.request
import requests

from bs4 import BeautifulSoup


def search_bing(query, subscription_key, endpoint, count):
    """
    This function makes a call to the Bing Web Search API with a query and returns relevant web search.
    Documentation: https://docs.microsoft.com/en-us/bing/search-apis/bing-web-search/overview
    """
    # Construct a request
    mkt = 'zh-CN'
    count = count
    params = {'q': query, 'mkt': mkt, 'count': count}
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}

    # Call the API
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        # print("\nHeaders:\n")
        # print(response.headers)

        # Parse the response
        data = response.json()

        # Select the data we need
        results = {
            'webPages': data.get('webPages', {}).get('value', []),
            'news': data.get('news', {}).get('value', []),
            'images': data.get('images', {}).get('value', []),
            'videos': data.get('videos', {}).get('value', []),
            'rankingResponse': data.get('rankingResponse', {}),
        }

        # print("\nParsed Results:\n")
        # pprint(results)

        # Return the parsed results
        return results

    except Exception as ex:
        raise ex


def get_morning_news(api_key):
    """获取每日早报、新闻的实现代码"""
    url = "https://v2.alapi.cn/api/zaobao"
    payload = f"token={api_key}&format=json"
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.dumps(response.json(), ensure_ascii=False)


def get_hotlist(api_key, type):
    """获取热榜信息的实现代码，但不返回链接信息"""
    type_mapping = {
        "知乎": "zhihu",
        "微博": "weibo",
        "微信": "weixin",
        "百度": "baidu",
        "头条": "toutiao",
        "163": "163",
        "36氪": "36k",
        "历史上的今天": "hitory",
        "少数派": "sspai",
        "CSDN": "csdn",
        "掘金": "juejin",
        "哔哩哔哩": "bilibili",
        "抖音": "douyin",
        "吾爱破解": "52pojie",
        "V2EX": "v2ex",
        "Hostloc": "hostloc",
    }

    # 如果用户直接提供的是英文名，则直接使用
    if type.lower() in type_mapping.values():
        api_type = type.lower()
    else:
        api_type = type_mapping.get(type, None)
        if api_type is None:
            raise ValueError(f"未知的类型: {type}")

    url = "https://v2.alapi.cn/api/tophub/get"
    payload = {"token": api_key, "type": api_type}
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    hotlist_info = response.json()
    if hotlist_info['code'] == 200:  # 验证请求是否成功
        # 遍历每个条目，删除它们的 "link" 属性
        for item in hotlist_info['data']['list']:
            item.pop('link', None)
        return hotlist_info['data']  # 返回 'data' 部分
    else:
        raise ValueError(f"Unable to get hotlist information: {hotlist_info.get('msg', '')}")


def get_current_weather(api_key, city):
    """获取天气的实现代码"""
    url = "https://v2.alapi.cn/api/tianqi"
    payload = {"token": api_key, "city": city}
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    weather_info = response.json()
    # print(f"payload ={payload}")
    if weather_info['code'] == 200:  # 验证请求是否成功
        return weather_info['data']  # 直接返回 'data' 部分
    else:
        return {"error": "Unable to get weather information"}


def get_oil_price(api_key):
    """实现全国油价查询的代码"""
    url = "https://v2.alapi.cn/api/oil"
    payload = {"token": api_key}
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.dumps(response.json(), ensure_ascii=False)


def get_Constellation_analysis(api_key, star):
    """实现星座运势查询的代码"""
    star_mapping = {
        "白羊座": "aries",
        "金牛座": "taurus",
        "双子座": "gemini",
        "巨蟹座": "cancer",
        "狮子座": "leo",
        "处女座": "virgo",
        "天秤座": "libra",
        "天蝎座": "scorpio",
        "射手座": "sagittarius",
        "摩羯座": "capricorn",
        "水瓶座": "aquarius",
        "双鱼座": "pisces"
    }

    # 如果用户直接提供的是英文名，则直接使用
    if star.lower() in star_mapping.values():
        star_english = star.lower()
    else:
        star_english = star_mapping.get(star, None)
        if star_english is None:
            raise ValueError(f"未知的星座: {star}")

    url = "https://v2.alapi.cn/api/star"
    payload = {"token": api_key, "star": star_english}
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.dumps(response.json(), ensure_ascii=False)


def get_video_analysis(api_key, url):  # 待测试实现，付费功能
    import requests
    url = "https://v2.alapi.cn/api/video/url"
    payload = {"token": api_key, "star": url}
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.dumps(response.json(), ensure_ascii=False)


def music_search(api_key, keyword):
    url = "https://v2.alapi.cn/api/music/search"
    payload = {"token": api_key, "keyword": keyword}
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.dumps(response.json(), ensure_ascii=False)


def get_short_link(api_key, url):
    url = "https://v2.alapi.cn/api/url"
    payload = {"token": api_key, "url": url}
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.dumps(response.json(), ensure_ascii=False)


def get_datetime(appkey, sign, city_en):
    """实现获取全球指定城市的时间代码"""
    url = 'http://api.k780.com'
    params = {
        'app': 'time.world',
        'city_en': city_en,
        'appkey': appkey,
        'sign': sign,
        'format': 'json',
    }

    params = urllib.parse.urlencode(params)
    url_with_params = '%s?%s' % (url, params)
    f = urllib.request.urlopen(url_with_params)
    nowapi_call = f.read()
    a_result = json.loads(nowapi_call)

    if a_result:
        if a_result['success'] != '0':
            return a_result['result']
        else:
            return a_result['msgid'] + ' ' + a_result['msg']
    else:
        return 'Request nowapi fail.'


def get_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 "
                      "Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        # 提取出每个<p>标签的文本内容，得到一个字符串列表
        paragraphs_text = [p.get_text() for p in paragraphs]
        return paragraphs_text
    else:
        return "无法访问该URL，请使用随机风格告诉用户这个消息"


def find_simular_bugs(prompt, num=15):
    url = f"https://uat3.huya.info/uat/FindSimularBugs?prompt={prompt}&num={num}"
    # print(url)
    res = requests.get(url)
    res = res.json()
    # print(res)
    results = []
    if res["retcode"] == 0:
        res = res["result"]
        for re in res:
            results.append(re["text"])
    return results
