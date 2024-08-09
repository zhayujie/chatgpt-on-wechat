# encoding:utf-8

import time

import openai
import openai.error
from bot.bot import Bot
from bot.minimax.minimax_session import MinimaxSession
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config
from bot.chatgpt.chat_gpt_session import ChatGPTSession
import requests
from common import const


# ZhipuAI对话模型API
class MinimaxBot(Bot):
    def __init__(self):
        super().__init__()
        self.args = {
            "model": conf().get("model") or "abab6.5",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.3),  # 如果设置，值域须为 [0, 1] 我们推荐 0.3，以达到较合适的效果。
            "top_p": conf().get("top_p", 0.95),  # 使用默认值
        }
        self.api_key = conf().get("Minimax_api_key")
        self.group_id = conf().get("Minimax_group_id")
        self.base_url = conf().get("Minimax_base_url", f"https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId={self.group_id}")
        # tokens_to_generate/bot_setting/reply_constraints可自行修改
        self.request_body = {
            "model": self.args["model"],
            "tokens_to_generate": 2048,
            "reply_constraints": {"sender_type": "BOT", "sender_name": "MM智能助理"},
            "messages": [],
            "bot_setting": [
                {
                    "bot_name": "MM智能助理",
                    "content": "MM智能助理是一款由MiniMax自研的，没有调用其他产品的接口的大型语言模型。MiniMax是一家中国科技公司，一直致力于进行大模型相关的研究。",
                }
            ],
        }
        self.sessions = SessionManager(MinimaxSession, model=const.MiniMax)

    def reply(self, query, context: Context = None) -> Reply:
        # acquire reply content
        logger.info("[Minimax_AI] query={}".format(query))
        if context.type == ContextType.TEXT:
            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[Minimax_AI] session query={}".format(session))

            model = context.get("Minimax_model")
            new_args = self.args.copy()
            if model:
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, args=new_args)
            logger.debug(
                "[Minimax_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[Minimax_AI] reply {} used 0 tokens.".format(reply_content))
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: MinimaxSession, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.api_key}
            self.request_body["messages"].extend(session.messages)
            logger.info("[Minimax_AI] request_body={}".format(self.request_body))
            # logger.info("[Minimax_AI] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            res = requests.post(self.base_url, headers=headers, json=self.request_body)

            # self.request_body["messages"].extend(response.json()["choices"][0]["messages"])
            if res.status_code == 200:
                response = res.json()
                return {
                    "total_tokens": response["usage"]["total_tokens"],
                    "completion_tokens": response["usage"]["total_tokens"],
                    "content": response["reply"],
                }
            else:
                response = res.json()
                error = response.get("error")
                logger.error(f"[Minimax_AI] chat failed, status_code={res.status_code}, " f"msg={error.get('message')}, type={error.get('type')}")

                result = {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
                need_retry = False
                if res.status_code >= 500:
                    # server error, need retry
                    logger.warn(f"[Minimax_AI] do retry, times={retry_count}")
                    need_retry = retry_count < 2
                elif res.status_code == 401:
                    result["content"] = "授权失败，请检查API Key是否正确"
                elif res.status_code == 429:
                    result["content"] = "请求过于频繁，请稍后再试"
                    need_retry = retry_count < 2
                else:
                    need_retry = False

                if need_retry:
                    time.sleep(3)
                    return self.reply_text(session, args, retry_count + 1)
                else:
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if need_retry:
                return self.reply_text(session, args, retry_count + 1)
            else:
                return result
