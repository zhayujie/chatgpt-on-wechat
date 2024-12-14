from common.expired_dict import ExpiredDict
from common.log import logger
from config import conf
from bot.database_manager import DatabaseManager


class Session(object):
    def __init__(self, session_id, system_prompt=None):
        self.session_id = session_id
        self.messages = []
        if system_prompt is None:
            self.system_prompt = conf().get("character_desc", "")
        else:
            self.system_prompt = system_prompt
        self.reset()  # Initialize with system prompt

    # 重置会话
    def reset(self):
        logger.info(f"[Session] Resetting session {self.session_id}")
        # Remove all existing system messages
        self.messages = [msg for msg in self.messages if msg['role'] != 'system']
        # Add the current system prompt
        system_item = {"role": "system", "content": self.system_prompt}
        self.messages.insert(0, system_item)

    def set_system_prompt(self, system_prompt):
        logger.info(f"[Session] Setting new system prompt for session {self.session_id}")
        self.system_prompt = system_prompt
        self.reset()

    def add_query(self, query):
        logger.debug(f"[Session] Adding query to session {self.session_id}")
        user_item = {"role": "user", "content": query}
        self.messages.append(user_item)

    def add_reply(self, reply):
        logger.debug(f"[Session] Adding reply to session {self.session_id}")
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
        logger.info("[SessionManager] Initializing DatabaseManager")
        self.db_manager = DatabaseManager()
        # Load existing sessions from database
        logger.info("[SessionManager] Loading sessions from database")
        stored_sessions = self.db_manager.load_all_sessions(sessioncls)
        # 正确处理 ExpiredDict
        if isinstance(self.sessions, ExpiredDict):
            for session_id, session in stored_sessions.items():
                self.sessions[session_id] = session
        else:
            self.sessions.update(stored_sessions)
        logger.info(f"[SessionManager] Loaded {len(stored_sessions)} sessions from database")

    def build_session(self, session_id, system_prompt=None):
        """
        如果session_id不在sessions中，创建一个新的session并添加到sessions中
        如果system_prompt不会空，会更新session的system_prompt并重置session
        """
        if session_id is None:
            logger.debug("[SessionManager] Creating temporary session with no ID")
            session = self.sessioncls(session_id, system_prompt, **self.session_args)
            return session

        try:
            session = self.sessions.get(session_id)
        except (KeyError, TypeError):
            session = None

        if session is None:
            # Try to load from database first
            logger.info(f"[SessionManager] Session {session_id} not in memory, trying to load from database")
            session = self.db_manager.load_session(session_id, self.sessioncls)
            if session is None:
                logger.info(f"[SessionManager] Creating new session {session_id}")
                session = self.sessioncls(session_id, system_prompt, **self.session_args)
            # 使用字典的 __setitem__ 方法来确保正确存储
            self.sessions[session_id] = session
        elif system_prompt is not None:
            logger.info(f"[SessionManager] Updating system prompt for session {session_id}")
            session.set_system_prompt(system_prompt)
            # Save session after updating system prompt
            self.db_manager.save_session(session)
            # 更新后重新存储到 sessions 中
            self.sessions[session_id] = session
        return session

    def session_query(self, query, session_id):
        session = self.build_session(session_id)
        session.add_query(query)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            total_tokens = session.discard_exceeding(max_tokens, None)
            logger.debug("prompt tokens used={}".format(total_tokens))
            # Save session after adding query
            logger.info(f"[SessionManager] Saving session {session_id} after query")
            self.db_manager.save_session(session)
        except Exception as e:
            logger.error(f"[SessionManager] Error in session_query for session {session_id}: {str(e)}")
            raise
        return session

    def session_reply(self, reply, session_id, total_tokens=None):
        session = self.build_session(session_id)
        session.add_reply(reply)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
            logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
            # Save session to database after reply
            logger.info(f"[SessionManager] Saving session {session_id} to database")
            self.db_manager.save_session(session)
        except Exception as e:
            logger.error(f"[SessionManager] Error in session_reply for session {session_id}: {str(e)}")
            raise
        return session

    def clear_session(self, session_id):
        if session_id in self.sessions:
            logger.info(f"[SessionManager] Clearing session {session_id}")
            self.db_manager.delete_session(session_id)
            del self.sessions[session_id]

    def clear_all_session(self):
        logger.info("[SessionManager] Clearing all sessions")
        self.db_manager.clear_all_sessions()
        self.sessions.clear()
