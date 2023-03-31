import asyncio
import re
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

            def func():
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(voice_file.to_file(self.content),loop).result()
            self._prepare_fn = func
            
        else:
            raise NotImplementedError("Unsupported message type: {}".format(wechaty_msg.type()))
        
        from_contact = wechaty_msg.talker()  # 获取消息的发送者
        self.from_user_id = from_contact.contact_id
        self.from_user_nickname = from_contact.name

        # group中的from和to，wechaty跟itchat含义不一样
        # wecahty: from是消息实际发送者, to:所在群
        # itchat: 如果是你发送群消息，from和to是你自己和所在群，如果是别人发群消息，from和to是所在群和你自己
        # 但这个差别不影响逻辑，group中只使用到：1.用from来判断是否是自己发的，2.actual_user_id来判断实际发送用户
        
        if self.is_group:
            self.to_user_id = room.room_id
            self.to_user_nickname = await room.topic()
        else:
            to_contact = wechaty_msg.to()
            self.to_user_id = to_contact.contact_id
            self.to_user_nickname = to_contact.name

        if self.is_group or wechaty_msg.is_self(): # 如果是群消息，other_user设置为群，如果是私聊消息，而且自己发的，就设置成对方。
            self.other_user_id = self.to_user_id
            self.other_user_nickname = self.to_user_nickname
        else:
            self.other_user_id = self.from_user_id
            self.other_user_nickname = self.from_user_nickname

        

        if self.is_group: # wechaty群聊中，实际发送用户就是from_user
            self.is_at = await wechaty_msg.mention_self()
            if not self.is_at: # 有时候复制粘贴的消息，不算做@，但是内容里面会有@xxx，这里做一下兼容
                name = wechaty_msg.wechaty.user_self().name
                pattern = f'@{name}(\u2005|\u0020)'
                if re.search(pattern,self.content):
                    logger.debug(f'wechaty message {self.msg_id} include at')
                    self.is_at = True

            self.actual_user_id = self.from_user_id
            self.actual_user_nickname = self.from_user_nickname
