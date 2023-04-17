# -*- coding: utf-8 -*-#
# filename: receive.py
import xml.etree.ElementTree as ET

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger


def parse_xml(web_data):
    if len(web_data) == 0:
        return None
    xmlData = ET.fromstring(web_data)
    return WeChatMPMessage(xmlData)


class WeChatMPMessage(ChatMessage):
    def __init__(self, xmlData):
        super().__init__(xmlData)
        self.to_user_id = xmlData.find("ToUserName").text
        self.from_user_id = xmlData.find("FromUserName").text
        self.create_time = xmlData.find("CreateTime").text
        self.msg_type = xmlData.find("MsgType").text
        try:
            self.msg_id = xmlData.find("MsgId").text
        except:
            self.msg_id = self.from_user_id + self.create_time
        self.is_group = False

        # reply to other_user_id
        self.other_user_id = self.from_user_id

        if self.msg_type == "text":
            self.ctype = ContextType.TEXT
            self.content = xmlData.find("Content").text.encode("utf-8")
        elif self.msg_type == "voice":
            self.ctype = ContextType.TEXT
            self.content = xmlData.find("Recognition").text.encode("utf-8")  # 接收语音识别结果
        elif self.msg_type == "image":
            # not implemented
            self.pic_url = xmlData.find("PicUrl").text
            self.media_id = xmlData.find("MediaId").text
        elif self.msg_type == "event":
            self.content = xmlData.find("Event").text
        else:  # video, shortvideo, location, link
            # not implemented
            pass
