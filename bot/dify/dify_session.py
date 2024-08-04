from common.expired_dict import ExpiredDict
from config import conf


class DifySession(object):
    def __init__(self, session_id: str, user: str, conversation_id: str=''):
        self.__session_id = session_id
        self.__user = user
        self.__conversation_id = conversation_id
        self.__user_message_counter = 0

    def get_session_id(self):
        return self.__session_id

    def get_user(self):
        return self.__user

    def get_conversation_id(self):
        return self.__conversation_id

    def set_conversation_id(self, conversation_id):
        self.__conversation_id = conversation_id

    def count_user_message(self):
        if conf().get("dify_conversation_max_messages", 5) <= 0:
            # 当设置的最大消息数小于等于0，则不限制
            return
        if self.__user_message_counter >= conf().get("dify_conversation_max_messages", 5):
            self.__user_message_counter = 0
            # FIXME: dify目前不支持设置历史消息长度，暂时使用超过5条清空会话的策略，缺点是没有滑动窗口，会突然丢失历史消息
            self.__conversation_id = ''
        
        self.__user_message_counter += 1

class DifySessionManager(object):
    def __init__(self, sessioncls, **session_kwargs):
        if conf().get("expires_in_seconds"):
            sessions = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            sessions = dict()
        self.sessions = sessions
        self.sessioncls = sessioncls
        self.session_kwargs = session_kwargs

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

    def get_session(self, session_id, user):
        session = self._build_session(session_id, user)
        return session

    def clear_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_all_session(self):
        self.sessions.clear()
