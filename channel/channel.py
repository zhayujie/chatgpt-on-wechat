"""
Message sending channel abstract class
"""

from bridge.bridge import Bridge
from bridge.context import Context
from bridge.reply import *
from bridge.omni import save_url2omni

class Channel(object):
    channel_type = ""
    NOT_SUPPORT_REPLYTYPE = [ReplyType.VOICE, ReplyType.IMAGE]

    def startup(self):
        """
        init channel
        """
        raise NotImplementedError

    def handle_text(self, msg):
        """
        process received msg
        :param msg: message object
        """
        raise NotImplementedError

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        """
        send message to user
        :param msg: message content
        :param receiver: receiver channel account
        :return:
        """
        raise NotImplementedError

    def build_reply_content(self, query, context: Context = None) -> Reply:
        return Bridge().fetch_reply_content(query, context)

    def build_voice_to_text(self, voice_file) -> Reply:
        return Bridge().fetch_voice_to_text(voice_file)

    def build_text_to_voice(self, text) -> Reply:
        return Bridge().fetch_text_to_voice(text)

    def build_my_text_info(self, context: Context = None) -> Reply:
        """
        构建文本回复，包含保存链接的结果。
        return: Reply（直接构建的文本回复）
        """
        result = save_url2omni(context)

        # 使用get方法获取嵌套字典的值，避免 KeyError
        url = result.get("saveUrl", {}).get("url")

        if url:
            return Reply(ReplyType.TEXT, f"链接保存成功，现在阅读: {url}")
        else:
            return Reply(ReplyType.TEXT, "链接保存失败")