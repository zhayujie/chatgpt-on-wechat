from common.expired_dict import ExpiredDict
from common.log import logger
from config import conf
import requests

class Session(object):
    def __init__(self, session_id, system_prompt=None):
        self.session_id = session_id
        self.messages = []
        self.channelId = ""
        if system_prompt is None:
            self.system_prompt = conf().get("character_desc", "")
        else:
            self.system_prompt = system_prompt
        if conf().get("coze_discord_proxy", False):
            if self.channelId != "":
                self.delete_discord_channel()
            self.channelId = self.create_discord_channel(session_id)

    # create a new discord channel
    def create_discord_channel(self,session_id):
        base_url = conf().get("open_ai_api_base")
        # base_url 去掉最后的"v1"
        base_url = base_url[:-2]
        url = "{}api/channel/create".format(base_url)
        parent_id = conf().get("coze_discord_proxy_parent_id", "")
        data = {"parentId":parent_id, "name":session_id, "type": 0}        
        headers = {'proxy-secret': conf().get("open_ai_api_key", ""), 'out-time': '1200'}
        response = requests.post(url, json=data, headers=headers)
        print(response.json())
        channelId = response.json().get("data").get("id")   
        return channelId
    
    def delete_discord_channel(self):
        base_url = conf().get("open_ai_api_base")
        # base_url 去掉最后的"v1"
        base_url = base_url[:-2]
        url_delete = "{}api/channel/del/{}".format(base_url, self.channelId)
        headers = {'proxy-secret': conf().get("open_ai_api_key", ""), 'out-time': '1200'}
        requests.get(url_delete, headers=headers)
    
    # 重置会话
    def reset(self):
        system_item = {"role": "system", "content": self.system_prompt}
        self.messages = [system_item]
        if conf().get("coze_discord_proxy", False):
            self.delete_discord_channel()
            self.channelId = self.create_discord_channel(self.session_id)

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.reset()
        print("=====reset in function set_system_prompt=====")

    def add_query(self, query):
        user_item = {"role": "user", "content": query}
        self.messages.append(user_item)

    def add_reply(self, reply):
        assistant_item = {"role": "assistant", "content": reply}
        self.messages.append(assistant_item)

    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        raise NotImplementedError

    def calc_tokens(self):
        raise NotImplementedError


class SessionManager(object):
    def __init__(self, sessioncls, **session_args):
        if conf().get("expires_in_seconds"):
            sessions = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            sessions = dict()
        self.sessions = sessions
        self.sessioncls = sessioncls
        self.session_args = session_args

    def build_session(self, session_id, system_prompt=None):
        """
        如果session_id不在sessions中，创建一个新的session并添加到sessions中
        如果system_prompt不会空，会更新session的system_prompt并重置session
        """
        if session_id is None:
            return self.sessioncls(session_id, system_prompt, **self.session_args)

        if session_id not in self.sessions:
            self.sessions[session_id] = self.sessioncls(session_id, system_prompt, **self.session_args)
        elif system_prompt is not None:  # 如果有新的system_prompt，更新并重置session
            self.sessions[session_id].set_system_prompt(system_prompt)
        session = self.sessions[session_id]
        return session

    def session_query(self, query, session_id):
        session = self.build_session(session_id)
        session.add_query(query)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            total_tokens = session.discard_exceeding(max_tokens, None)
            logger.debug("prompt tokens used={}".format(total_tokens))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session

    def session_reply(self, reply, session_id, total_tokens=None):
        session = self.build_session(session_id)
        session.add_reply(reply)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
            logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for session: {}".format(str(e)))
        return session

    def clear_session(self, session_id):
        if session_id in self.sessions:
            if conf().get("coze_discord_proxy", False):
                self.sessions[session_id].delete_discord_channel()
            del self.sessions[session_id]

    def clear_all_session(self):
        for session_id in self.sessions:
            self.clear_session(session_id)
