from channel.chat_message import ChatMessage
from bridge.context import ContextType
from channel.nonebot.bean.nonebot_raw_message import NoneBotRawMessage
from nonebot.adapters.onebot.v11 import Bot


class NoneBotMessage(ChatMessage):
    """
    NoneBotMessage 对 NoneBot 消息的封装
    """
    def __init__(self, msg: NoneBotRawMessage, bot: Bot):
        super().__init__(msg)
        self.bot = bot
        """
        bot -> 机器人对象，用于此条消息后续的回复
        """
        self.msg_id = msg.msg_id
        self.create_time = msg.create_time
        self.is_group = msg.is_group
        self.from_user_id = msg.from_user_id
        self.from_user_nickname = msg.from_user_nickname
        self.to_user_id = msg.to_user_id
        self.to_user_nickname = msg.to_user_nickname
        self.other_user_id = msg.group_id if msg.is_group else msg.from_user_id
        self.other_user_nickname = None if msg.is_group else msg.from_user_nickname
        self.actual_user_id = msg.from_user_id
        self.actual_user_nickname = msg.from_user_nickname

        # 对消息类型进行填充
        if msg.ctype == "text":
            self.ctype = ContextType.TEXT
            self.content = msg.content
        elif msg.ctype == "voice":
            self.ctype = ContextType.VOICE
            self.content = msg.content
        elif msg.ctype == "image":
            self.ctype = ContextType.IMAGE
            self.content = msg.content
        else:
            raise NotImplementedError(f"Unsupported message type: Type: {msg.ctype}")

        # 对群组消息的信息填充
        if msg.is_group:
            self.group_id = msg.group_id
            self.group_nickname = msg.group_nickname
            self.is_at = msg.is_at

