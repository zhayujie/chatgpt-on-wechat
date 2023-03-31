

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.tmp_dir import TmpDir
from common.log import logger
from lib.itchat.content import *
from lib import itchat

class WeChatMessage(ChatMessage):

    def __init__(self, itchat_msg, is_group=False):
        super().__init__( itchat_msg)
        self.msg_id = itchat_msg['MsgId']
        self.create_time = itchat_msg['CreateTime']
        self.is_group = is_group
        
        if itchat_msg['Type'] == TEXT:
            self.ctype = ContextType.TEXT
            self.content = itchat_msg['Text']
        elif itchat_msg['Type'] == VOICE:
            self.ctype = ContextType.VOICE
            self.content = TmpDir().path() + itchat_msg['FileName']  # content直接存临时目录路径
            self._prepare_fn = lambda: itchat_msg.download(self.content)
        else:
            raise NotImplementedError("Unsupported message type: {}".format(itchat_msg['Type']))
        
        self.from_user_id = itchat_msg['FromUserName']
        self.to_user_id = itchat_msg['ToUserName']
        
        user_id = itchat.instance.storageClass.userName
        nickname = itchat.instance.storageClass.nickName
        
        # 虽然from_user_id和to_user_id用的少，但是为了保持一致性，还是要填充一下
        # 以下很繁琐，一句话总结：能填的都填了。
        if self.from_user_id == user_id:
            self.from_user_nickname = nickname
        if self.to_user_id == user_id:
            self.to_user_nickname = nickname
        try: # 陌生人时候, 'User'字段可能不存在
            self.other_user_id = itchat_msg['User']['UserName']
            self.other_user_nickname = itchat_msg['User']['NickName']
            if self.other_user_id == self.from_user_id:
                self.from_user_nickname = self.other_user_nickname
            if self.other_user_id == self.to_user_id:
                self.to_user_nickname = self.other_user_nickname
        except KeyError as e: # 处理偶尔没有对方信息的情况
            logger.warn("[WX]get other_user_id failed: " + str(e))
            if self.from_user_id == user_id:
                self.other_user_id = self.to_user_id
            else:
                self.other_user_id = self.from_user_id

        if self.is_group:
            self.is_at = itchat_msg['IsAt']
            self.actual_user_id = itchat_msg['ActualUserName']
            self.actual_user_nickname = itchat_msg['ActualNickName']
