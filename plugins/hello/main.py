# encoding:utf-8

import plugins
from plugins import *
from common.log import logger


@plugins.register(name="Hello", desc="A simple plugin that says hello", version="0.1", author="lanvent")
class Hello(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        # self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[hello] inited")

    def on_handle_context(self, e_context: EventContext):

        logger.debug("on_handle_context. content: %s" % e_context['context']['content'])

        if e_context['context']['content'] == "Hello":
            e_context['reply']['type'] = "TEXT"
            msg = e_context['context']['msg']
            if e_context['context']['isgroup']:
                e_context['reply']['content'] = "Hello, " + msg['ActualNickName'] + " from " + msg['User'].get('NickName', "Group")
            else:
                e_context['reply']['content'] = "Hello, " + msg['User'].get('NickName', "My friend")
            
            e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑

        if e_context['context']['content'] == "Hi":
            e_context['reply']['type'] = "TEXT"
            e_context['reply']['content'] = "Hi"
            e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑，一般会覆写reply

        if e_context['context']['content'] == "End":
            # 如果是文本消息"End"，将请求转换成"IMAGE_CREATE"，并将content设置为"The World"
            if e_context['context']['type'] == "TEXT":
                e_context['context']['type'] = "IMAGE_CREATE"
                e_context['context']['content'] = "The World"
                e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
