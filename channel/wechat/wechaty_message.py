from wechaty import MessageType
from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.tmp_dir import TmpDir
from common.log import logger
from wechaty.user import Message

class aobject(object):
    """Inheriting this class allows you to define an async __init__.

    So you can create objects by doing something like `await MyClass(params)`
    """
    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self):
        pass

class WechatyMessage(ChatMessage, aobject):

    async def __init__(self, wechaty_msg: Message):
        super().__init__(wechaty_msg)
        
        room = wechaty_msg.room()

        self.msg_id = wechaty_msg.message_id
        self.create_time = wechaty_msg.payload.timestamp
        self.is_group = room is not None
        
        if wechaty_msg.type() == MessageType.MESSAGE_TYPE_TEXT:
            self.ctype = ContextType.TEXT
            self.content = wechaty_msg.text()
        elif wechaty_msg.type() == MessageType.MESSAGE_TYPE_AUDIO:
            self.ctype = ContextType.VOICE
            voice_file = await wechaty_msg.to_file_box()
            self.content = TmpDir().path() + voice_file.name  # content直接存临时目录路径
            self._prepare_fn = lambda: voice_file.to_file(self.content)
        else:
            raise NotImplementedError("Unsupported message type: {}".format(wechaty_msg.type()))
        
        from_contact = wechaty_msg.talker()  # 获取消息的发送者
        self.from_user_id = from_contact.contact_id
        self.from_user_nickname = from_contact.name
        
        if self.is_group:
            self.to_user_id = room.room_id
            self.to_user_nickname = await room.topic()
        else:
            to_contact = wechaty_msg.to()
            self.to_user_id = to_contact.contact_id
            self.to_user_nickname = to_contact.name

        if wechaty_msg.is_self():
            self.other_user_id = self.to_user_id
            self.other_user_nickname = self.to_user_nickname
        else:
            self.other_user_id = self.from_user_id
            self.other_user_nickname = self.from_user_nickname

        if self.is_group:
            self.is_at = await wechaty_msg.mention_self()
            self.actual_user_id = self.other_user_id
            self.actual_user_nickname = self.other_user_nickname
