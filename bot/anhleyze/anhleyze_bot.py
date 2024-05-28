# encoding:utf-8

import time

import openai
# import openai.error

from bot.bot import Bot
# from bot.openai.open_ai_image import OpenAIImage
# from bot.openai.open_ai_session import OpenAISession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from requests.exceptions import ChunkedEncodingError
user_session = dict()

import re,json,requests

# OpenAI对话模型API (可用)
class AnhLeyzeBot(Bot):
    def __init__(self):
        super().__init__()
        # openai.api_key = conf().get("open_ai_api_key")
        # if conf().get("open_ai_api_base"):
        #     openai.api_base = conf().get("open_ai_api_base")
        # proxy = conf().get("proxy")
        # if proxy:
        #     openai.proxy = proxy

        # self.sessions = SessionManager(OpenAISession, model=conf().get("model") or "text-davinci-003")
        # self.args = {
        #     "model": conf().get("model") or "text-davinci-003",  # 对话模型的名称
        #     "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
        #     "max_tokens": 1200,  # 回复最大的字符数
        #     "top_p": 1,
        #     "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        #     "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        #     "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
        #     "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        #     "stop": ["\n\n\n"],
        # }

    def reply(self, query, context=None):
        # acquire reply content
        print(context)
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[OPEN_AI] query={}".format(query))
                session_id = context["session_id"]
                reply = None
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                elif query == "#清除所有":
                    self.sessions.clear_all_session()
                    reply = Reply(ReplyType.INFO, "所有人记忆已清除")
                else:
                    # session = self.sessions.session_query(query, session_id)
                    result = self.reply_text(query)
                    reply = Reply(ReplyType.TEXT, result)
                    # total_tokens, completion_tokens, reply_content = (
                    #     result["total_tokens"],
                    #     result["completion_tokens"],
                    #     result["content"],
                    # )
                    # logger.debug(
                    #     "[OPEN_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(str(session), session_id, reply_content, completion_tokens)
                    # )

                    # if total_tokens == 0:
                    #     reply = Reply(ReplyType.ERROR, reply_content)
                    # else:
                    #     self.sessions.session_reply(reply_content, session_id, total_tokens)
                    #     reply = Reply(ReplyType.TEXT, reply_content)
                return reply
            elif context.type == ContextType.IMAGE_CREATE:
                ok, retstring = self.create_img(query, 0)
                reply = None
                if ok:
                    reply = Reply(ReplyType.IMAGE_URL, retstring)
                else:
                    reply = Reply(ReplyType.ERROR, retstring)
                return reply

    def reply_text(self, query: str):
        refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImhlYWRtYXN0ZXIiLCJleHAiOjE3MTczNDExODJ9.bIXXlG0iTaew9s6jB8EcaU4zT9ogIWmO-ynoatDW_N4"
        refresh_headers = {
                'Authorization': f'Bearer {refresh_token}',
                # 'Content-Type': 'application/json'  # Assuming JSON data is being sent
                }
        auth_token = None
        headers = {}
        
        # file.write("Question, Result\n")
        # for d in data:
            
            # print(d)
        d = {
        'message': f'{query}',
        'language': 'EN',
        # Add more data fields as needed
        }
        try:
            auth_token = requests.get("https://backend.anhsin.pro/refresh-token",headers=refresh_headers)
            auth_token = auth_token.json()["accessToken"]
            headers = {
                'Authorization': f'Bearer {auth_token}',
                # 'Content-Type': 'application/json'  # Assuming JSON data is being sent
            }
            response = requests.post("https://chatbot.anhsin.pro/chatbot" + "/store", json=d, headers=headers)
            # print(response.status_code)
            print(response.text)
            # Check if the request was successful (status code 200)
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
        try:
            # auth_token = requests.get("https://backend.anhsin.pro/refresh-token",headers=refresh_headers)
            # auth_token = auth_token.json()["accessToken"]
            # headers = {
            #     'Authorization': f'Bearer {auth_token}',
            #     # 'Content-Type': 'application/json'  # Assuming JSON data is being sent
            # }
            # print(url, headers)
            response = requests.get("https://chatbot.anhsin.pro/chatbot" + '/', headers=headers)
        except ChunkedEncodingError as e:
            print(e)
            time.sleep(1)

        if response.status_code == 200:
                # Print the response content
            pass
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
        try:
            for line in response.iter_lines():
                if line:
                    # Decode the JSON line
                    # Update the last response
                    last_response = line

            # file.write(f"""\"{d["message"]}\", \"{last_response}\"\n""")
            # print(type(last_response))
            # print(last_response)
            
            match = re.search(rb'\{.*?\}', last_response)
            if match:
                response = match.group().decode('utf-8')
                print(json.loads(response)["data"])
                return json.loads(response)["data"]
            else:
                print("No match found")
                return "Error"
        except Exception as e:
            print(e)
            return "Error"
        # break
