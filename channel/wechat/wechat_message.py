import re

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir
from lib import itchat
from lib.itchat.content import *

class WechatMessage(ChatMessage):
    def __init__(self, itchat_msg, is_group=False):
        super().__init__(itchat_msg)
        self.msg_id = itchat_msg["MsgId"]
        self.create_time = itchat_msg["CreateTime"]
        self.is_group = is_group

        notes_join_group = ["加入群聊", "加入了群聊", "invited", "joined"]  # 可通过添加对应语言的加入群聊通知中的关键词适配更多
        notes_bot_join_group = ["邀请你", "invited you", "You've joined", "你通过扫描"]
        notes_exit_group = ["移出了群聊", "removed"]  # 可通过添加对应语言的踢出群聊通知中的关键词适配更多
        notes_patpat = ["拍了拍我", "tickled my", "tickled me"] # 可通过添加对应语言的拍一拍通知中的关键词适配更多

        if itchat_msg["Type"] == TEXT:
            self.ctype = ContextType.TEXT
            self.content = itchat_msg["Text"]
        elif itchat_msg["Type"] == VOICE:
            self.ctype = ContextType.VOICE
            self.content = TmpDir().path() + itchat_msg["FileName"]  # content直接存临时目录路径
            self._prepare_fn = lambda: itchat_msg.download(self.content)
        elif itchat_msg["Type"] == PICTURE and itchat_msg["MsgType"] == 3:
            self.ctype = ContextType.IMAGE
            self.content = TmpDir().path() + itchat_msg["FileName"]  # content直接存临时目录路径
            self._prepare_fn = lambda: itchat_msg.download(self.content)
        elif itchat_msg["Type"] == NOTE and itchat_msg["MsgType"] == 10000:
            if is_group:
                if any(note_bot_join_group in itchat_msg["Content"] for note_bot_join_group in notes_bot_join_group):  # 邀请机器人加入群聊
                    logger.warn("机器人加入群聊消息，不处理~")
                    pass
                elif any(note_join_group in itchat_msg["Content"] for note_join_group in notes_join_group): # 若有任何在notes_join_group列表中的字符串出现在NOTE中
                # 这里只能得到nickname， actual_user_id还是机器人的id
                    if "加入群聊" not in itchat_msg["Content"]:
                        self.ctype = ContextType.JOIN_GROUP
                        self.content = itchat_msg["Content"]
                        if "invited" in itchat_msg["Content"]: # 匹配英文信息
                            self.actual_user_nickname = re.findall(r'invited\s+(.+?)\s+to\s+the\s+group\s+chat', itchat_msg["Content"])[0]
                        elif "joined" in itchat_msg["Content"]: # 匹配通过二维码加入的英文信息
                            self.actual_user_nickname = re.findall(r'"(.*?)" joined the group chat via the QR Code shared by', itchat_msg["Content"])[0]
                        elif "加入了群聊" in itchat_msg["Content"]:
                            self.actual_user_nickname = re.findall(r"\"(.*?)\"", itchat_msg["Content"])[-1]
                    elif "加入群聊" in itchat_msg["Content"]:
                        self.ctype = ContextType.JOIN_GROUP
                        self.content = itchat_msg["Content"]
                        self.actual_user_nickname = re.findall(r"\"(.*?)\"", itchat_msg["Content"])[0]

                elif any(note_exit_group in itchat_msg["Content"] for note_exit_group in notes_exit_group):  # 若有任何在notes_exit_group列表中的字符串出现在NOTE中
                    self.ctype = ContextType.EXIT_GROUP
                    self.content = itchat_msg["Content"]
                    self.actual_user_nickname = re.findall(r"\"(.*?)\"", itchat_msg["Content"])[0]
                    
            elif "你已添加了" in itchat_msg["Content"]:  #通过好友请求
                self.ctype = ContextType.ACCEPT_FRIEND
                self.content = itchat_msg["Content"]
            elif any(note_patpat in itchat_msg["Content"] for note_patpat in notes_patpat):  # 若有任何在notes_patpat列表中的字符串出现在NOTE中:
                self.ctype = ContextType.PATPAT
                self.content = itchat_msg["Content"]
                if is_group:
                    if "拍了拍我" in itchat_msg["Content"]:  # 识别中文
                        self.actual_user_nickname = re.findall(r"\"(.*?)\"", itchat_msg["Content"])[0]
                    elif ("tickled my" in itchat_msg["Content"] or "tickled me" in itchat_msg["Content"]):
                        self.actual_user_nickname = re.findall(r'^(.*?)(?:tickled my|tickled me)', itchat_msg["Content"])[0]
            else:
                raise NotImplementedError("Unsupported note message: " + itchat_msg["Content"])
        elif itchat_msg["Type"] == ATTACHMENT:
            self.ctype = ContextType.FILE
            self.content = TmpDir().path() + itchat_msg["FileName"]  # content直接存临时目录路径
            self._prepare_fn = lambda: itchat_msg.download(self.content)
        elif itchat_msg["Type"] == SHARING:
            self.ctype = ContextType.SHARING
            self.content = itchat_msg.get("Url")

        else:
            raise NotImplementedError("Unsupported message type: Type:{} MsgType:{}".format(itchat_msg["Type"], itchat_msg["MsgType"]))

        self.from_user_id = itchat_msg["FromUserName"]
        self.to_user_id = itchat_msg["ToUserName"]

        user_id = itchat.instance.storageClass.userName
        nickname = itchat.instance.storageClass.nickName

        # 虽然from_user_id和to_user_id用的少，但是为了保持一致性，还是要填充一下
        # 以下很繁琐，一句话总结：能填的都填了。
        if self.from_user_id == user_id:
            self.from_user_nickname = nickname
        if self.to_user_id == user_id:
            self.to_user_nickname = nickname
        try:  # 陌生人时候, User字段可能不存在
            # my_msg 为True是表示是自己发送的消息
            self.my_msg = itchat_msg["ToUserName"] == itchat_msg["User"]["UserName"] and \
                          itchat_msg["ToUserName"] != itchat_msg["FromUserName"]
            self.other_user_id = itchat_msg["User"]["UserName"]
            self.other_user_nickname = itchat_msg["User"]["NickName"]
            if self.other_user_id == self.from_user_id:
                self.from_user_nickname = self.other_user_nickname
            if self.other_user_id == self.to_user_id:
                self.to_user_nickname = self.other_user_nickname
            if itchat_msg["User"].get("Self"):
                # 自身的展示名，当设置了群昵称时，该字段表示群昵称
                self.self_display_name = itchat_msg["User"].get("Self").get("DisplayName")
        except KeyError as e:  # 处理偶尔没有对方信息的情况
            logger.warn("[WX]get other_user_id failed: " + str(e))
            if self.from_user_id == user_id:
                self.other_user_id = self.to_user_id
            else:
                self.other_user_id = self.from_user_id

        if self.is_group:
            self.is_at = itchat_msg["IsAt"]
            self.actual_user_id = itchat_msg["ActualUserName"]
            if self.ctype not in [ContextType.JOIN_GROUP, ContextType.PATPAT, ContextType.EXIT_GROUP]:
                self.actual_user_nickname = itchat_msg["ActualNickName"]
