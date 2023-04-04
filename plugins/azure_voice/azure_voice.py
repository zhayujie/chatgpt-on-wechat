import plugins
from plugins import *
from common.log import logger
from bridge.reply import *
from bridge.context import *
from channel.channel import Channel
from config import conf


@plugins.register(name="Azure_voice", desc="一个根据前缀来合成对应语言的语音的插件", version="0.1", author="luluo123",
                  desire_priority=0)
class Azure_voice_reply(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Azure_voice] inited")

    def on_handle_context(self, e_context: EventContext):
        # 判断是否为文本消息,如果不是则跳过
        if e_context['context'].type != ContextType.TEXT:
            return
        # 获取文本消息
        if conf().get("text_to_voice") != "azure":
            return
        text = e_context['context'].content
        logger.debug("[Hello] on_handle_context. content: %s" % text)
        # 判断是否包含前缀
        if text.startswith("$"):
            reply = Reply()
            # 在文本的第二个”$“之后的内容为context的content
            e_context['context'].content = text.split("$", 2)[2]
            langue = text.split("$")[1].split("$")[0]
            channel = Channel()
            #给每个问题加上“用(选择的语种)回复：“是为了触发chatgpt生成对应的文本
            e_context['context'].content = "用" + langue+"回复：" + e_context['context'].content
            reply = channel.build_reply_content(e_context['context'].content, e_context['context'])
            reply.content = "#"+langue+"#"+reply.content
            reply = channel.build_text_to_voice(reply.content)
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS
            logger.info("调用了azure_voice插件")
        else:
            return
