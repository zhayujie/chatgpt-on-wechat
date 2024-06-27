from common.expired_dict import ExpiredDict
from common.log import logger
from config import conf


class Session(object):
    def __init__(self, session_id, system_prompt=None):
        self.session_id = session_id
        self.messages = []
        if system_prompt is None:
            self.system_prompt = conf().get("character_desc", "")
        else:
            self.system_prompt = system_prompt

    # 重置会话
    def reset(self):
        system_item = {"role": "system", "content": self.system_prompt}
        self.messages = [system_item]

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.reset()

    def add_query(self, query):
        user_item = {"role": "user", "content": query}
        self.messages.append(user_item)

    def add_reply(self, reply):
        assistant_item = {"role": "assistant", "content": reply}
        self.messages.append(assistant_item)
# add
    def get_text_to_process(self):
        # 返回需要处理的文本
        return " ".join([msg["content"] for msg in self.messages])

#gpt4修改
    def discard_exceeding(self, max_tokens, tokenizer):
        text = self.get_text_to_process()
        if not isinstance(text, str):
            text = str(text)  # 确保 text 是字符串
        tokens = tokenizer.encode(text)
        if len(tokens) > max_tokens:
            self.trim_text(tokens[:max_tokens])
        return len(tokens)
    
#原来代码 def discard_exceeding(self, max_tokens=None, cur_tokens=None):
#        raise NotImplementedError

#gpt4修改
    def trim_text(self, tokens):
        # 将修剪后的 tokens 转换回文本并更新 messages
        trimmed_text = tokenizer.decode(tokens)
        self.messages = [{"role": "system", "content": self.system_prompt}] + [{"role": "user", "content": trimmed_text}]
    
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

#修改后代码,注意这里需要linkai定义一个tokenizer的获取函数，但是不知道是放在那里，或者直接加上
    def session_query(self, query, session_id):
        session = self.build_session(session_id)
        session.add_query(query)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            tokenizer = get_tokenizer()  # 假设我们有一个获取 tokenizer 的方法
            total_tokens = session.discard_exceeding(max_tokens, tokenizer)
            logger.debug("prompt tokens used={}".format(total_tokens))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session

    def session_reply(self, reply, session_id, total_tokens=None):
        session = self.build_session(session_id)
        session.add_reply(reply)
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            tokenizer = get_tokenizer()  # 假设我们有一个获取 tokenizer 的方法
            tokens_cnt = session.discard_exceeding(max_tokens, tokenizer)
            logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for session: {}".format(str(e)))
        return session

#原来代码
    # def session_query(self, query, session_id):
    #     session = self.build_session(session_id)
    #     session.add_query(query)
    #     try:
    #         max_tokens = conf().get("conversation_max_tokens", 1000)
    #         total_tokens = session.discard_exceeding(max_tokens, None)
    #         logger.debug("prompt tokens used={}".format(total_tokens))
    #     except Exception as e:
    #         logger.warning("Exception when counting tokens precisely for prompt: {}".format(str(e)))
    #     return session

    # def session_reply(self, reply, session_id, total_tokens=None):
    #     session = self.build_session(session_id)
    #     session.add_reply(reply)
    #     try:
    #         max_tokens = conf().get("conversation_max_tokens", 1000)
    #         tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
    #         logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
    #     except Exception as e:
    #         logger.warning("Exception when counting tokens precisely for session: {}".format(str(e)))
    #     return session

    def clear_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_all_session(self):
        self.sessions.clear()
