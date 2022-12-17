import time
from bot.bot import Bot
from revChatGPT.revChatGPT import Chatbot
from common.log import logger
from config import conf

user_session = dict()
last_session_refresh = time.time()


# ChatGPT web接口 (暂时不可用)
class ChatGPTBot(Bot):
    def __init__(self):
        config = {
            "Authorization": "<Your Bearer Token Here>",  # This is optional
            "session_token": conf().get("session_token")
        }
        self.chatbot = Chatbot(config)

    def reply(self, query, context=None):

        from_user_id = context['from_user_id']
        logger.info("[GPT]query={}, user_id={}, session={}".format(query, from_user_id, user_session))

        now = time.time()
        global last_session_refresh
        if now - last_session_refresh > 60 * 8:
            logger.info('[GPT]session refresh, now={}, last={}'.format(now, last_session_refresh))
            self.chatbot.refresh_session()
        last_session_refresh = now

        if from_user_id in user_session:
            if time.time() - user_session[from_user_id]['last_reply_time'] < 60 * 5:
                self.chatbot.conversation_id = user_session[from_user_id]['conversation_id']
                self.chatbot.parent_id = user_session[from_user_id]['parent_id']
            else:
                self.chatbot.reset_chat()
        else:
            self.chatbot.reset_chat()

        logger.info("[GPT]convId={}, parentId={}".format(self.chatbot.conversation_id, self.chatbot.parent_id))

        try:
            res = self.chatbot.get_chat_response(query, output="text")
            logger.info("[GPT]userId={}, res={}".format(from_user_id, res))

            user_cache = dict()
            user_cache['last_reply_time'] = time.time()
            user_cache['conversation_id'] = res['conversation_id']
            user_cache['parent_id'] = res['parent_id']
            user_session[from_user_id] = user_cache
            return res['message']
        except Exception as e:
            logger.error(e)
            return None
