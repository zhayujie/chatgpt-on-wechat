# encoding:utf-8

import json
import time
from typing import List, Tuple

import openai
import openai.error
import broadscope_bailian
from broadscope_bailian import ChatQaMessage

from bot.bot import Bot
from bot.ali.ali_qwen_session import AliQwenSession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common import const
from config import conf, load_config
import dashscope

class AliQwenBot(Bot):
    def __init__(self):
        super().__init__()
        # self.api_key_expired_time = self.set_api_key()
        self.sessions = SessionManager(AliQwenSession, model=conf().get("model", const.QWEN))

    # def api_key_client(self):
    #     return broadscope_bailian.AccessTokenClient(access_key_id=self.access_key_id(), access_key_secret=self.access_key_secret())
    #

    def api_key(self):
        return conf().get("qwen_api_key")

    # def access_key_id(self):
    #     return conf().get("qwen_access_key_id")
    #
    # def access_key_secret(self):
    #     return conf().get("qwen_access_key_secret")
    #
    # def agent_key(self):
    #     return conf().get("qwen_agent_key")
    #
    # def app_id(self):
    #     return conf().get("qwen_app_id")
    #
    # def node_id(self):
    #     return conf().get("qwen_node_id", "")

    def temperature(self):
        return conf().get("temperature", 0.2 )

    def top_p(self):
        return conf().get("top_p", 1)

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[QWEN] query={}".format(query))

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
            logger.debug("[QWEN] session query={}".format(session.messages))

            reply_content = self.reply_text(session)
            logger.debug(
                "[QWEN] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
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
                logger.debug("[QWEN] reply {} used 0 tokens.".format(reply_content))
            return reply

        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: AliQwenSession, retry_count=0) -> dict:
        """
        call bailian's ChatCompletion to get the answer
        :param session: a conversation session
        :param retry_count: retry count
        :return: {}
        """
        try:
            # prompt, history = self.convert_messages_format(session.messages)
            # self.update_api_key_if_expired()
            # NOTE 阿里百炼的call()函数未提供temperature参数，考虑到temperature和top_p参数作用相同，取两者较小的值作为top_p参数传入，详情见文档 https://help.aliyun.com/document_detail/2587502.htm
            # response = broadscope_bailian.Completions().call(app_id=self.app_id(), prompt=prompt, history=history, top_p=min(self.temperature(), self.top_p()))

            # SDK升级，采用更简洁高效的方式，见：https://github.com/zhayujie/chatgpt-on-wechat/issues/1836
            # 接入文档：https://help.aliyun.com/zh/dashscope/developer-reference/api-details
            # TODO 模型暂时默认取 qwen-turbo, 后面可在config.json['model']里配置
            turbo = dashscope.Generation.Models.qwen_turbo
            dashscope.api_key = self.api_key()
            response = dashscope.Generation.call(turbo, messages=session.messages, result_format='message', top_p=min(self.temperature(), self.top_p()))
            completion_content = self.get_completion_content(response)
            completion_tokens, total_tokens = self.calc_tokens(session.messages, completion_content)
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": completion_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.error.RateLimitError):
                logger.warn("[QWEN] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.error.Timeout):
                logger.warn("[QWEN] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIError):
                logger.warn("[QWEN] Bad Gateway: {}".format(e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, openai.error.APIConnectionError):
                logger.warn("[QWEN] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                logger.exception("[QWEN] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[QWEN] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result

    # def set_api_key(self):
    #     api_key, expired_time = self.api_key_client().create_token(agent_key=self.agent_key())
    #     broadscope_bailian.api_key = api_key
    #     return expired_time

    def update_api_key_if_expired(self):
        if time.time() > self.api_key_expired_time:
            self.api_key_expired_time = self.set_api_key()

    # def convert_messages_format(self, messages) -> Tuple[str, List[ChatQaMessage]]:
    #     history = []
    #     user_content = ''
    #     assistant_content = ''
    #     system_content = ''
    #     for message in messages:
    #         role = message.get('role')
    #         if role == 'user':
    #             user_content += message.get('content')
    #         elif role == 'assistant':
    #             assistant_content = message.get('content')
    #             history.append(ChatQaMessage(user_content, assistant_content))
    #             user_content = ''
    #             assistant_content = ''
    #         elif role =='system':
    #             system_content += message.get('content')
    #     if user_content == '':
    #         raise Exception('no user message')
    #     if system_content != '':
    #         # NOTE 模拟系统消息，测试发现人格描述以"你需要扮演ChatGPT"开头能够起作用，而以"你是ChatGPT"开头模型会直接否认
    #         system_qa = ChatQaMessage(system_content, '好的，我会严格按照你的设定回答问题')
    #         history.insert(0, system_qa)
    #     logger.debug("[QWEN] converted qa messages: {}".format([item.to_dict() for item in history]))
    #     logger.debug("[QWEN] user content as prompt: {}".format(user_content))
    #     return user_content, history

    def get_completion_content(self, response):
        if not response.status_code == 200:
            return f"[ERROR]\n{response.status_code}:{response.message}"
        text = response.output.choices[0]['message']['content']
        # 响应结构如下
        # {
        #     "status_code": 200,
        #     "request_id": "2f661bdf-6780-9329-ba0b-cabcdc949959",
        #     "code": "",
        #     "message": "",
        #     "output": {
        #         "text": null,
        #         "finish_reason": null,
        #         "choices": [
        #             {
        #                 "finish_reason": "stop",
        #                 "message": {
        #                     "role": "assistant",
        #                     "content": "当然可以。如果你不喜欢或者不打算使用糖，那么在炖煮过程中可以省略糖的部分。不过，糖在炖牛腩的过程中可以中和牛肉的腥味，并且能让菜肴色泽红亮，增加甜度，使得口感更加醇厚。如果不加糖，你可以在最后几分钟加入一些番茄酱或者醋来提升菜肴的风味。这样也能达到类似的效果。"
        #                 }
        #             }
        #         ]
        #     },
        #     "usage": {
        #         "input_tokens": 376,
        #         "output_tokens": 81,
        #         "total_tokens": 457
        #     }
        # }
        return text

    def calc_tokens(self, messages, completion_content):
        completion_tokens = len(completion_content)
        prompt_tokens = 0
        for message in messages:
            prompt_tokens += len(message["content"])
        return completion_tokens, prompt_tokens + completion_tokens
