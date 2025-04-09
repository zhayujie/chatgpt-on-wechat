# encoding:utf-8

"""
wechat channel message
"""

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from wcferry import WxMsg


class WechatfMessage(ChatMessage):
    """
    微信消息封装类
    """

    def __init__(self, channel, wcf_msg: WxMsg, is_group=False):
        """
        初始化消息对象
        :param wcf_msg: wcferry消息对象
        :param is_group: 是否是群消息
        """
        super().__init__(wcf_msg)
        self.msg_id = wcf_msg.id
        self.create_time = wcf_msg.ts  # 使用消息时间戳
        self.is_group = is_group or wcf_msg._is_group
        self.wxid = channel.wxid
        self.name = channel.name

        # 解析消息类型
        if wcf_msg.is_text():
            self.ctype = ContextType.TEXT
            self.content = wcf_msg.content
        else:
            raise NotImplementedError(f"Unsupported message type: {wcf_msg.type}")

        # 设置发送者和接收者信息
        self.from_user_id = self.wxid if wcf_msg.sender == self.wxid else wcf_msg.sender
        self.from_user_nickname = self.name if wcf_msg.sender == self.wxid else channel.contact_cache.get_name_by_wxid(wcf_msg.sender)
        self.to_user_id = self.wxid
        self.to_user_nickname = self.name
        self.other_user_id = wcf_msg.sender
        self.other_user_nickname = channel.contact_cache.get_name_by_wxid(wcf_msg.sender)

        # 群消息特殊处理
        if self.is_group:
            self.other_user_id = wcf_msg.roomid
            self.other_user_nickname = channel.contact_cache.get_name_by_wxid(wcf_msg.roomid)
            self.actual_user_id = wcf_msg.sender
            self.actual_user_nickname = channel.wcf.get_alias_in_chatroom(wcf_msg.sender, wcf_msg.roomid)
            if not self.actual_user_nickname:  # 群聊获取不到企微号成员昵称，这里尝试从联系人缓存去获取
                self.actual_user_nickname = channel.contact_cache.get_name_by_wxid(wcf_msg.sender)
            self.room_id = wcf_msg.roomid
            self.is_at = wcf_msg.is_at(self.wxid)  # 是否被@当前登录用户

        # 判断是否是自己发送的消息
        self.my_msg = wcf_msg.from_self()
