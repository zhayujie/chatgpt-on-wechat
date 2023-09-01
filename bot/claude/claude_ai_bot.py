import re
import time
import json
import uuid
from curl_cffi import requests
from bot.bot import Bot
from bot.claude.claude_ai_session import ClaudeAiSession
from bot.openai.open_ai_image import OpenAIImage
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf


class ClaudeAIBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(ClaudeAiSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.claude_api_cookie = conf().get("claude_api_cookie")
        self.proxy = conf().get("proxy")
        self.con_uuid_dic = {}
        if self.proxy:
            self.proxies = {
            "http": self.proxy,
            "https": self.proxy
        }
        else:
            self.proxies = None
        self.org_uuid = self.get_organization_id()

    def generate_uuid(self):
        random_uuid = uuid.uuid4()
        random_uuid_str = str(random_uuid)
        formatted_uuid = f"{random_uuid_str[0:8]}-{random_uuid_str[9:13]}-{random_uuid_str[14:18]}-{random_uuid_str[19:23]}-{random_uuid_str[24:]}"
        return formatted_uuid

    def get_uuid(self):
        if conf().get("claude_uuid") != None:
            self.con_uuid = conf().get("claude_uuid")
        else:
            con_uuid = self.generate_uuid()
            self.create_new_chat(con_uuid)

    def get_organization_id(self):
        url = "https://claude.ai/api/organizations"
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.claude_api_cookie}'
        }
        response = requests.get(url, headers=headers,impersonate="chrome110",proxies=self.proxies)
        res = json.loads(response.text)
        uuid = res[0]['uuid']
        return uuid
        
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

    def get_organization_id(self):
        url = "https://claude.ai/api/organizations"
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'Cookie': f'{self.claude_api_cookie}'
        }
        try:
            response = requests.get(url, headers=headers,impersonate="chrome110",proxies =self.proxies )
            res = json.loads(response.text)
            uuid = res[0]['uuid']
        except:
            print(response.text)
        return uuid

    def conversation_share_check(self,session_id):
        if session_id not in self.con_uuid_dic:
            self.con_uuid_dic[session_id] = self.generate_uuid()
            self.create_new_chat(self.con_uuid_dic[session_id])
        return self.con_uuid_dic[session_id]

    def create_new_chat(self, con_uuid):
        url = f"https://claude.ai/api/organizations/{self.org_uuid}/chat_conversations"
        payload = json.dumps({"uuid": con_uuid, "name": ""})
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Cookie': self.claude_api_cookie,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers'
        }
        response = requests.post(url, headers=headers, data=payload,impersonate="chrome110", proxies= self.proxies)
        # Returns JSON of the newly created conversation information
        return response.json()
        
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
            logger.warn("[CLAUDEAI] failed after maximum number of retry times")
            return Reply(ReplyType.ERROR, "请再问我一次吧")

        try:
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            con_uuid = self.conversation_share_check(session_id)
            model = conf().get("model") or "gpt-3.5-turbo"
            # remove system message
            if session.messages[0].get("role") == "system":
                if model == "wenxin" or model == "claude":
                    session.messages.pop(0)
            logger.info(f"[CLAUDEAI] query={query}")

            # do http request
            base_url = "https://claude.ai"
            payload = json.dumps({
                "completion": {
                    "prompt": f"{query}",
                    "timezone": "Asia/Kolkata",
                    "model": "claude-2"
                },
                "organization_uuid": f"{self.org_uuid}",
                "conversation_uuid": f"{con_uuid}",
                "text": f"{query}",
                "attachments": []
            })
            headers = {
                'User-Agent':
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                'Accept': 'text/event-stream, text/event-stream',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://claude.ai/chats',
                'Content-Type': 'application/json',
                'Origin': 'https://claude.ai',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Cookie': f'{self.claude_api_cookie}',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'TE': 'trailers'
            }

            res = requests.post(base_url + "/api/append_message", headers=headers, data=payload,impersonate="chrome110",proxies= self.proxies,timeout=400)
            if res.status_code == 200 or "pemission" in res.text:
                # execute success
                decoded_data = res.content.decode("utf-8")
                decoded_data = re.sub('\n+', '\n', decoded_data).strip()
                data_strings = decoded_data.split('\n')
                completions = []
                for data_string in data_strings:
                    json_str = data_string[6:].strip()
                    data = json.loads(json_str)
                    if 'completion' in data:
                        completions.append(data['completion'])

                reply_content = ''.join(completions)
                logger.info(f"[CLAUDE] reply={reply_content}, total_tokens=invisible")

                self.sessions.session_reply(reply_content, session_id, 100)
                return Reply(ReplyType.TEXT, reply_content)
            else:
                response = res.json()
                error = response.get("error")
                logger.error(f"[CLAUDE] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}, detail: {res.text}, uuid: {con_uuid}")

                if res.status_code >= 500:
                    # server error, need retry
                    time.sleep(2)
                    logger.warn(f"[CLAUDE] do retry, times={retry_count}")
                    return self._chat(query, context, retry_count + 1)
                return Reply(ReplyType.ERROR, "提问太快啦，请休息一下再问我吧")

        except Exception as e:
            logger.exception(e)
            # retry
            time.sleep(2)
            logger.warn(f"[CLAUDE] do retry, times={retry_count}")
            return self._chat(query, context, retry_count + 1)
