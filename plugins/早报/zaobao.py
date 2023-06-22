import requests
import json
import re
import plugins
from bridge.reply import Reply, ReplyType
from plugins import *


@plugins.register(
    name="DailyNews",
    desire_priority=1,
    hidden=False,
    desc="A plugin that fetches daily news",
    version="0.1",
    author="YourName",
)
class DailyNews(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        print("[DailyNews] inited")

    def on_handle_context(self, e_context: EventContext):
        content = e_context["context"].content
        if content == "早报":
            url = "https://v2.alapi.cn/api/zaobao"
            # https://alapi.cn/  在这里申请你的token
            payload = "token=<再次填写你的token>&format=json"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}

            try:
                response = requests.request("POST", url, data=payload, headers=headers)
                response.raise_for_status()  # Raise an error if the status code is not 200
            except requests.exceptions.RequestException as e:
                print(f"An error occurred when making the request: {e}")
                return

            data = json.loads(response.text)
            news_data = data.get('data')
            if news_data:
                date = news_data.get('date')
                news = news_data.get('news')
                weiyu = news_data.get('weiyu')

                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"日期: {date}\n新闻:\n"
                for i, news_item in enumerate(news, 1):
                    news_item = re.sub(r'^\d+[、.]\s*', '', news_item)
                    reply.content += f"{i}. {news_item}\n"
                reply.content += f"\n微语: {weiyu}"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                print("ERROR: Data not found in response")

    def get_help_text(self, **kwargs):
        help_text = "输入 '早报'，我会为你抓取每日新闻\n"
        return help_text
