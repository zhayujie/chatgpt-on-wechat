# encoding:utf-8

from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config
from .dashscope_session import DashscopeSession
import os
import dashscope
from dashscope import Application
from http import HTTPStatus



dashscope_models = {
    "qwen-turbo": dashscope.Generation.Models.qwen_turbo,
    "qwen-plus": dashscope.Generation.Models.qwen_plus,
    "qwen-max": dashscope.Generation.Models.qwen_max,
    "qwen-bailian-v1": dashscope.Generation.Models.bailian_v1
}
# 百炼AI对话模型API
class DashscopeBot(Bot):
    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(DashscopeSession, model=conf().get("model") or "qwen-plus")
        self.model_name = conf().get("model") or "qwen-plus"
        self.api_key = conf().get("dashscope_api_key")
        self.app_id = conf().get("dashscope_app_id")
        os.environ["DASHSCOPE_API_KEY"] = self.api_key
        self.client = dashscope.Generation

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[DASHSCOPE] query={}".format(query))

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
            logger.debug("[DASHSCOPE] session query={}".format(session.messages))

            reply_content = self.reply_text(session, context=context, query=query)
            logger.debug(
                "[DASHSCOPE] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
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
                logger.debug("[DASHSCOPE] reply {} used 0 tokens.".format(reply_content))
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: DashscopeSession, retry_count=0, context=None, query=None) -> dict:
        """
        支持模型对话和应用调用的统一回复方法
        :param session: a conversation session
        :param retry_count: retry count
        :param context: 上下文参数
        :param query: 用户原始问题
        :return: {}
        """
        try:
            dashscope_app_id = None
            if self.app_id is not None:
                dashscope_app_id = self.app_id
            if dashscope_app_id:
                # 应用调用模式
                dashscope.api_key = self.api_key
                try:
                    response = Application.call(
                        api_key=self.api_key,
                        app_id=dashscope_app_id,
                        prompt=query or (session.messages[-1]["content"] if session.messages else "")
                    )
                    if response.status_code == HTTPStatus.OK:
                        return {
                            "total_tokens": 0,
                            "completion_tokens": 1,
                            "content": response.output.text,
                        }
                    else:
                        logger.error(f"[DASHSCOPE_APP] request_id={response.request_id}, code={response.status_code}, message={response.message}")
                        return {"completion_tokens": 0, "content": response.message, "total_tokens": 0}
                except Exception as e:
                    logger.exception(e)
                    return {"completion_tokens": 0, "content": "应用调用异常，请稍后重试", "total_tokens": 0}
            # 默认走原有模型对话
            dashscope.api_key = self.api_key
            response = self.client.call(
                dashscope_models[self.model_name],
                messages=session.messages,
                result_format="message"
            )
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0]["message"]["content"]
                return {
                    "total_tokens": response.usage["total_tokens"],
                    "completion_tokens": response.usage["output_tokens"],
                    "content": content,
                }
            else:
                logger.error('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                    response.request_id, response.status_code,
                    response.code, response.message
                ))
                result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧", "total_tokens": 0}
                need_retry = retry_count < 2
                if need_retry:
                    return self.reply_text(session, retry_count + 1, context=context, query=query)
                else:
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧", "total_tokens": 0}
            if need_retry:
                return self.reply_text(session, retry_count + 1, context=context, query=query)
            else:
                return result
