import json
import requests
import plugins
from bridge.reply import Reply
from bridge.reply import ReplyType
from plugins import *

zodiac_dict = {
    '白羊座': 'aries',
    '金牛座': 'taurus',
    '双子座': 'gemini',
    '巨蟹座': 'cancer',
    '狮子座': 'leo',
    '处女座': 'virgo',
    '天秤座': 'libra',
    '天蝎座': 'scorpio',
    '射手座': 'sagittarius',
    '摩羯座': 'capricorn',
    '水瓶座': 'aquarius',
    '双鱼座': 'pisces'
}

@plugins.register(
    name="Horoscope",
    desire_priority=1,
    hidden=False,
    desc="A plugin that fetches daily horoscope",
    version="0.1",
    author="YourName",
)
class Horoscope(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        print("[Horoscope] inited")
    
    def on_handle_context(self, e_context: EventContext):
        content = e_context["context"].content
        if content.startswith("运势"):
            parts = content.split(" ")
            self.command = parts[1]
            user_data = zodiac_dict[self.command]
            url = "https://v2.alapi.cn/api/star"
            payload = f"token=NdEUedYlsXta5EDz&star={user_data}"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}

            try:
                response = requests.request("POST", url, data=payload, headers=headers)
                response.raise_for_status()  # Raise an error if the status code is not 200
            except requests.exceptions.RequestException as e:
                print(f"An error occurred when making the request: {e}")
                return
            
            data = json.loads(response.text)
            star_data = data.get('data')['day']
            star_data1 = data.get('data')['week']
            if star_data:
                ji = star_data.get('ji')#忌
                yi = star_data.get('yi')#宜
                notice = star_data.get('notice')#本日提醒
                date = star_data.get('date')#更新日期
                all = star_data.get('all')#综合运势
                all_text = star_data.get('all_text')#综合运势说明
                love = star_data.get('love')#爱情指数
                love_text = star_data.get('love_text')#爱情指数说明
                work = star_data.get('work')#事业指数
                work_text = star_data.get('work_text')
                health = star_data.get('health')#健康指数
                health_text = star_data.get('health_text')
                discuss = star_data.get('discuss')#商谈指数
                money = star_data.get('money')#财富指数
                money_text = star_data.get('money_text')
                lucky_star = star_data.get('lucky_star')#幸运星座
                lucky_color = star_data.get('lucky_color')#幸运颜色
                lucky_number = star_data.get('lucky_number')#幸运数字
                lucky_star1 = star_data1.get('lucky_star')#本周幸运星座
                take_star = star_data1.get('take_star')#本周提防星座

                reply = Reply()
                reply.type = ReplyType.TEXT
                reply.content = f"日期：{date}\n1.忌：{ji}\n2.宜：{yi}\n3.本日提醒：{notice}\n4.综合运势：{all}\n5.综合运势说明：{all_text}\n6.爱情指数：{love}\n7.爱情指数说明：{love_text}\n8.事业指数：{work}\n9.事业指数说明：{work_text}\n10.健康指数：{health}\n11.健康指数说明：{health_text}\n12.商谈指数：{discuss}\n13.财富指数：{money}\n14.财富指数说明：{money_text}\n15.幸运星座：{lucky_star}\n16.幸运颜色：{lucky_color}\n17.幸运数字：{lucky_number}\n18.本周幸运星座：{lucky_star1}\n20.本周提防星座：{take_star}"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                print("ERROR: Data not found in response")

    def get_help_text(self, **kwargs):
        help_text = "输入 '运势 星座'，我会为你占卜运势\n"
        return help_text





