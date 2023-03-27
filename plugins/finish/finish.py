# encoding:utf-8

from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
import plugins
from plugins import *
from common.log import logger


@plugins.register(name="Finish", desc="A plugin that check unknow command", version="1.0", author="js00000", desire_priority= -999)
class Finish(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Finish] inited")

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        logger.debug("[Finish] on_handle_context. content: %s" % content)
        if content.startswith("#"):
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = "未知指令\n查看指令列表请输入#help\n"
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑

    def get_help_text(self, **kwargs):
        return ""
