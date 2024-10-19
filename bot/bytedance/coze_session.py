from common.expired_dict import ExpiredDict
from config import conf
from common.log import logger


class CozeSession(object):
    def __init__(self, session_id: str, user_id: str, conversation_id=None, system_prompt=None):
        self.__session_id = session_id
        self.messages = []
        self.__user_id = user_id
        self.__user_message_counter = 0
        self.__conversation_id = conversation_id
        if system_prompt is None:
            self.system_prompt = conf().get("character_desc", "")
        else:
            self.system_prompt = system_prompt

    def add_query(self, query):
        user_item = {"role": "user", "content": query}
        self.messages.append(user_item)

    def add_reply(self, reply):
        assistant_item = {"role": "assistant", "content": reply}
        self.messages.append(assistant_item)

    def get_session_id(self):
        return self.__session_id

    def get_user_id(self):
        return self.__user_id

    def get_conversation_id(self):
        return self.__conversation_id

    def set_conversation_id(self, conversation_id):
        self.__conversation_id = conversation_id

    def get_session(self, session_id, user):
        session = self._build_session(session_id, user)
        return session

    def _build_session(self, session_id: str, user: str):
        """
        如果session_id不在sessions中，创建一个新的session并添加到sessions中
        """
        if session_id is None:
            return self.sessioncls(session_id, user)

        if session_id not in self.sessions:
            self.sessions[session_id] = self.sessioncls(session_id, user)
        session = self.sessions[session_id]
        return session

    def count_user_message(self):
        if conf().get("coze_conversation_max_messages", 5) <= 0:
            # 当设置的最大消息数小于等于0，则不限制
            return
        if self.__user_message_counter >= conf().get("coze_conversation_max_messages", 5):
            self.__user_message_counter = 0
            # FIXME: coze目前不支持设置历史消息长度，暂时使用超过5条清空会话的策略，缺点是没有滑动窗口，会突然丢失历史消息
            self.__conversation_id = ''

        self.__user_message_counter += 1


class CozeSessionManager(object):
    def __init__(self, sessioncls, **session_args):
        if conf().get("expires_in_seconds"):
            sessions = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            sessions = dict()
        self.sessions = sessions
        self.sessioncls = sessioncls
        self.session_args = session_args

    def _build_session(self, session_id: str, user_id: str, system_prompt=None):
        """
        如果session_id不在sessions中，创建一个新的session并添加到sessions中
        """
        if session_id is None:
            return self.sessioncls(session_id, user_id, system_prompt, **self.session_args)

        if session_id not in self.sessions:
            self.sessions[session_id] = self.sessioncls(session_id, user_id, system_prompt, **self.session_args)
        session = self.sessions[session_id]
        return session

    def session_query(self, query, user_id, session_id):
        session = self._build_session(session_id, user_id)
        session.add_query(query)
        # try:
        #     max_tokens = conf().get("conversation_max_tokens", 1000)
        #     total_tokens = session.discard_exceeding(max_tokens, None)
        #     logger.debug("prompt tokens used={}".format(total_tokens))
        # except Exception as e:
        #     logger.warning("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session

    def session_reply(self, reply, user_id, session_id, total_tokens=None):
        session = self._build_session(session_id, user_id)
        session.add_reply(reply)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
            logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for session: {}".format(str(e)))
        return session

    # def get_session(self, session_id, user_id):
    #     session = self._build_session(session_id, user_id)
    #     return session

    def clear_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_all_session(self):
        self.sessions.clear()
