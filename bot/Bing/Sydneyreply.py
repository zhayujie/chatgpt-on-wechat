import asyncio


from bot.bot import Bot
from bot.Bing.Sydney_session import SydneySession
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config

from bot.Bing import Sydney_proess

class SydneyBot(Bot):
    def __init__(self) -> None:
        super().__init__()
        self.sessions = SessionManager(SydneySession, model=conf().get("model") or "gpt-3.5-turbo")
        
    def reply(self, query, context: Context = None):
        if context.type == ContextType.TEXT:
            logger.info("[SYDNEY] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[SYDNEY] session query={}".format(session.messages))
            try:
                reply_content = asyncio.run(Sydney_proess.sydney_reply(session))
                self.sessions.session_reply(reply_content["content"], session_id)
                logger.debug(
                    "[SYDNEY] new_query={}, session_id={}, reply_cont={}".format(
                        session.messages,
                        session_id,
                        reply_content["content"],
                    )
                )
            except Exception:
                reply_content = asyncio.run(Sydney_proess.sydney_reply(session))
                self.sessions.session_reply(reply_content["content"], session_id)
            reply = Reply(ReplyType.TEXT, reply_content["content"])
            return reply