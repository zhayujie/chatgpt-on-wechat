import re
import time
import json
import uuid
from curl_cffi import requests
from bot.bot import Bot


from bot.chatgpt_hack.chatgpt_hack_session import ChatgptHackSession
from bot.openai.open_ai_image import OpenAIImage
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf

class ChatgptHackBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        self.url = "https://chat.openai.com/backend-api/conversation"
        self.sessions = SessionManager(ChatgptHackSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.proxy = conf().get("proxy")
        self.autho = conf().get("chatgpt_hack_autho")
        if self.proxy:
            self.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
        else:self.proxies = None
        self.error = ""
        self.paren_message_id = ""
        self.conversation_id = ""
        self.headers = {
            'authority': 'chat.openai.com',
            'accept': 'text/event-stream',
            'accept-language': 'en-US',
            'authorization': self.autho,
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'cookie': "",
            'origin': 'https://chat.openai.com',
            'pragma': 'no-cache',
            'referer': 'https://chat.openai.com',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69'
        }
        self.payload = {"action":"next",
                                "messages":[{"id":self.generate_uuid(),
                                             "author":{"role":"system"},
                                             "content":{"content_type":"text","parts":[""]}}],
                                "parent_message_id":self.generate_uuid(),
                                "model":"text-davinci-002",
                                "timezone_offset_min":-480,"suggestions":[],
                                "history_and_training_disabled":False,
                                "arkose_token":None}
        self.create_conversation(conf().get("character_desc", ""))

    def generate_uuid(self):
        random_uuid = uuid.uuid4()
        random_uuid_str = str(random_uuid)
        formatted_uuid = f"{random_uuid_str[0:8]}-{random_uuid_str[9:13]}-{random_uuid_str[14:18]}-{random_uuid_str[19:23]}-{random_uuid_str[24:]}"
        return formatted_uuid

    def create_conversation(self,prompt):
        self.payload["messages"][0]["content"]["parts"] = [prompt]
        try:
            base_payload = json.dumps(self.payload)
            r = requests.post(self.url, headers=self.headers, impersonate="chrome110", proxies =self.proxies, data = base_payload, verify = False)
            origin_res = r.text.encode('utf-8').decode('unicode_escape')
            res = json.loads(origin_res.split("data:")[-2].strip())
            con_id = res["conversation_id"]
            message_id = res["message_id"]
            self.paren_message_id = message_id
            self.conversation_id = con_id
        except Exception as file:
            logger.error("[CHATGPTHACKAI] origin_error: {}".format(origin_res))
            logger.error("[CHATGPTHACKAI] faied to create new conversion!")
            return None,None

    def send_message(self,role, message, parent_message_id, conversation_id):
        self.payload["messages"][0]["id"] = self.generate_uuid()
        self.payload["messages"][0]["author"]["role"] = role
        self.payload["messages"][0]["content"]["parts"] = [message]
        self.payload["conversation_id"] = conversation_id
        self.payload["parent_message_id"] = parent_message_id

        payload = json.dumps(self.payload)
        r = requests.post(self.url, headers=self.headers, impersonate="chrome110", proxies =self.proxies, data = payload)
        try:
            res = r.text.encode('utf-8').decode('unicode_escape').replace("\n","\\n")
            result = json.loads(re.findall('data: (?:.|\n)*?"error": null}',res)[-1][6:])
            answer = result["message"]["content"]["parts"][0]
            message_id = result["message"]["id"]
            self.paren_message_id = message_id
        except Exception as file:
            logger.error("[CHATGPTHACKAI] faied to send question!")
            return None
        return answer

    def reply(self, query, context: Context = None) -> Reply:
        if context.type == ContextType.TEXT:
            return self._chat(query, context)
        elif context.type == ContextType.IMAGE_CREATE:
            ok, res = self.create_img(query, 0)
            if ok:
                reply = Reply(ReplyType.IMAGE_URL, res)
            else:
                reply = Reply(ReplyType.ERROR, res)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def _chat(self, query, context, retry_count=0) -> Reply:
        """
        发起对话请求
        :param query: 请求提示词
        :param context: 对话上下文
        :param retry_count: 当前递归重试次数
        :return: 回复
        """
        if retry_count >= 2:
            # exit from retry 2 times
            logger.error("[CHATGPTHACKAI] failed after maximum number of retry times")
            return Reply(ReplyType.ERROR, "请再问我一次吧")

        try:
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            model = conf().get("model") or "gpt-3.5-turbo"
            # remove system message
            if session.messages[0].get("role") == "system":
                if model == "wenxin" or model == "claude" or model == "chatgpt_hack":
                    session.messages.pop(0)
            logger.info(f"[CHATGPTHACKAI] query={query}")
            answer = self.send_message("user", query, self.paren_message_id, self.conversation_id)
            if answer:
                logger.info(f"[CHATGPTHACKAI] reply={answer}, total_tokens=invisible")
                self.sessions.session_reply(answer, session_id, 100)
                return Reply(ReplyType.TEXT, answer)
            else:
                return Reply(ReplyType.ERROR, "返回失败")

        except Exception as e:
            logger.exception(e)
            time.sleep(2)
            logger.warn(f"[CLAUDE] do retry, times={retry_count}")
            return self._chat(query, context, retry_count + 1)
