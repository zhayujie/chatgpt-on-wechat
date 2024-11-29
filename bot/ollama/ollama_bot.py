"""
Ollama bot

@author JoyCc
@Date 2024/7/1
"""
# encoding:utf-8

from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
import requests, time


# ollama对话模型API (可用)
class OllamaBot(Bot):

    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("model"))
        self.base_url = conf().get("ollama_base_url")
        self.prot = conf().get("ollama_port")
        self.ollama_url = f"{self.base_url}:{self.prot}/api/chat"
        self.args = {
            "model": conf().get("model") or "llama3",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.3),  # 如果设置，值域须为 [0, 1] 我们推荐 0.3，以达到较合适的效果。
            "top_p": conf().get("top_p", 1.0),  # 使用默认值
        }

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[Ollama] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            if query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[Ollama] session query={}".format(session.messages))
            reply_content = self.reply_text(session, self.args)
            reply = Reply(ReplyType.TEXT, reply_content["content"])
            logger.debug(
                "[Ollama] new_query={}, session_id={}, reply_cont={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                )
            )
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session, args=None, retry_count=0) -> dict:
        """
        call Ollama's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            body = args
            body["messages"] = session.messages
            body["stream"] = False # 默认不流式输出
            logger.debug("[Ollama] body={}".format(body))
            # logger.info("[MOONSHOT_AI] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            res = requests.post(
                self.ollama_url,
                json=body
            )
            result = {}
            if res.status_code == 200:
                response = res.json()
                logger.debug("[Ollama] response={}".format(response))
                # logger.info("[Ollama] response={}".format(response))
                return {
                    "content": response["message"]["content"]
                }
            else:
                response = res.json()
                #error = response.get("error")
                result["content"] = f"[Ollama] chat failed, status code={res.status_code}"
                need_retry = False
                if res.status_code >= 500:
                    # server error, need retry
                    logger.warn(f"[Ollama] do retry, times={retry_count}")
                    need_retry = retry_count < 2
                else:
                    need_retry = False

                if need_retry:
                    time.sleep(1)
                    return self.reply_text(session, args, retry_count + 1)
                else:
                    logger.error(f"[Ollama] chat failed, status_code={res.status_code},result = {result}")
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if need_retry:
                return self.reply_text(session, args, retry_count + 1)
            else:
                return result