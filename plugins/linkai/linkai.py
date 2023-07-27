import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from config import conf
from plugins import *
from .midjourney import MJBot, TaskType

# 任务线程池
task_thread_pool = ThreadPoolExecutor(max_workers=4)


@plugins.register(
    name="linkai",
    desc="A plugin that supports knowledge base and midjourney drawing.",
    version="0.1.0",
    author="https://link-ai.tech",
)
class LinkAI(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.config = super().load_config()
        self.mj_bot = MJBot(self.config.get("midjourney"))
        logger.info("[LinkAI] inited")

    def on_handle_context(self, e_context: EventContext):
        """
        消息处理逻辑
        :param e_context: 消息上下文
        """
        context = e_context['context']
        if context.type not in [ContextType.TEXT, ContextType.IMAGE]:
            # filter content no need solve
            return

        mj_type = self.mj_bot.judge_mj_task_type(e_context)
        if mj_type:
            # MJ作图任务处理
            self.mj_bot.process_mj_task(mj_type, e_context)
            return

        if self._is_chat_task(e_context):
            self._process_chat_task(e_context)

    # LinkAI 对话任务处理
    def _is_chat_task(self, e_context: EventContext):
        context = e_context['context']
        # 群聊应用管理
        return self.config.get("knowledge_base") and context.kwargs.get("isgroup")

    def _process_chat_task(self, e_context: EventContext):
        """
        处理LinkAI对话任务
        :param e_context: 对话上下文
        """
        context = e_context['context']
        # 群聊应用管理
        group_name = context.kwargs.get("msg").from_user_nickname
        app_code = self._fetch_group_app_code(group_name)
        if app_code:
            context.kwargs['app_code'] = app_code

    def _fetch_group_app_code(self, group_name: str) -> str:
        """
        根据群聊名称获取对应的应用code
        :param group_name: 群聊名称
        :return: 应用code
        """
        knowledge_base_config = self.config.get("knowledge_base")
        if knowledge_base_config and knowledge_base_config.get("group_mapping"):
            app_code = knowledge_base_config.get("group_mapping").get(group_name) \
                       or knowledge_base_config.get("group_mapping").get("ALL_GROUP")
            return app_code

    def get_help_text(self, verbose=False, **kwargs):
        trigger_prefix = conf().get("plugin_trigger_prefix", "$")
        help_text = "利用midjourney来画图。\n"
        if not verbose:
            return help_text
        help_text += f"{trigger_prefix}mj 描述词1,描述词2 ... ： 利用描述词作画，参数请放在提示词之后。\n{trigger_prefix}mjimage 描述词1,描述词2 ... ： 利用描述词进行图生图，参数请放在提示词之后。\n{trigger_prefix}mjr ID: 对指定ID消息重新生成图片。\n{trigger_prefix}mju ID 图片序号: 对指定ID消息中的第x张图片进行放大。\n{trigger_prefix}mjv ID 图片序号: 对指定ID消息中的第x张图片进行变换。\n例如：\n\"{trigger_prefix}mj a little cat, white --ar 9:16\"\n\"{trigger_prefix}mjimage a white cat --ar 9:16\"\n\"{trigger_prefix}mju 1105592717188272288 2\""
        return help_text

    def _set_reply_text(self, content: str, e_context: EventContext, level: ReplyType=ReplyType.ERROR):
        reply = Reply(level, content)
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
