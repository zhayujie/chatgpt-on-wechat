import datetime
import json
import os
import re
import time

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from channel.wechatnt.nt_run import wechatnt
from channel.wechatnt.WechatImageDecoder import WechatImageDecoder
from common.log import logger


def ensure_file_ready(file_path, timeout=10, interval=0.5):
    """确保文件可读。

    :param file_path: 文件路径。
    :param timeout: 超时时间，单位为秒。
    :param interval: 检查间隔，单位为秒。
    :return: 文件是否可读。
    """
    start_time = time.time()
    while True:
        if os.path.exists(file_path) and os.access(file_path, os.R_OK):
            return True
        elif time.time() - start_time > timeout:
            return False
        else:
            time.sleep(interval)


def get_nickname(contacts, wxid):
    for contact in contacts:
        if contact['wxid'] == wxid:
            return contact['nickname']
    return None  # 如果没有找到对应的wxid，则返回None


def get_display_name_or_nickname(room_members, group_wxid, wxid):
    if group_wxid in room_members:
        for member in room_members[group_wxid]['member_list']:
            if member['wxid'] == wxid:
                return member['display_name'] if member['display_name'] else member['nickname']
    return None  # 如果没有找到对应的group_wxid或wxid，则返回None


class NtchatMessage(ChatMessage):
    def __init__(self, wechat, wechat_msg, is_group=False):
        try:
            super().__init__(wechat_msg)
            self.msg_id = wechat_msg['data'].get('from_wxid', wechat_msg['data'].get("room_wxid"))
            self.create_time = wechat_msg['data'].get("timestamp")
            self.is_group = is_group
            self.wechat = wechat

            # 获取一些可能多次使用的值
            current_dir = os.getcwd()
            login_info = self.wechat.get_login_info()
            nickname = login_info['nickname']
            user_id = login_info['wxid']

            # 从文件读取数据，并构建以 wxid 为键的字典
            with open(os.path.join(current_dir, "tmp", 'wx_contacts.json'), 'r', encoding='utf-8') as f:
                contacts = {contact['wxid']: contact['nickname'] for contact in json.load(f)}
            with open(os.path.join(current_dir, "tmp", 'wx_rooms.json'), 'r', encoding='utf-8') as f:
                rooms = {room['wxid']: room['nickname'] for room in json.load(f)}


            data = wechat_msg['data']
            self.from_user_id = data.get('from_wxid', data.get("room_wxid"))
            self.from_user_nickname = contacts.get(self.from_user_id)
            self.to_user_id = user_id
            self.to_user_nickname = nickname
            self.other_user_nickname = self.from_user_nickname
            self.other_user_id = self.from_user_id

            if wechat_msg["type"] == 11046:  # 文本消息类型
                self.ctype = ContextType.TEXT
                self.content = data['msg']
            elif wechat_msg["type"] == 11047:  # 需要缓存文件的消息类型
                image_path = data.get('image').replace('\\', '/')
                if ensure_file_ready(image_path):
                    decoder = WechatImageDecoder(image_path)
                    self.ctype = ContextType.IMAGE
                    self.content = decoder.decode()
                    self._prepare_fn = lambda: None
                else:
                    logger.error(f"Image file {image_path} is not ready.")
            elif wechat_msg["type"] == 11048:  # 需要缓存文件的消息类型
                self.ctype = ContextType.VOICE
                self.content = data.get('mp3_file')
                self._prepare_fn = lambda: None
            elif wechat_msg["type"] == 11098:
                self.ctype = ContextType.JOIN_GROUP
                self.actual_user_nickname = data['member_list'][0]['nickname']
                self.content = f"{self.actual_user_nickname}加入了群聊！"
                directory = os.path.join(os.getcwd(), "tmp")
                result = {}
                for room_wxid in rooms.keys():
                    room_members = wechatnt.get_room_members(room_wxid)
                    result[room_wxid] = room_members
                with open(os.path.join(directory, 'wx_room_members.json'), 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
            elif wechat_msg["type"] == 11058 and "拍了拍我" in data.get('raw_msg'):
                self.ctype = ContextType.PATPAT
                self.content = data.get('raw_msg')
                if self.is_group:
                    directory = os.path.join(os.getcwd(), "tmp")
                    file_path = os.path.join(directory, "wx_room_members.json")
                    with open(file_path, 'r', encoding='utf-8') as file:
                        room_members = json.load(file)
                    self.actual_user_nickname = get_display_name_or_nickname(room_members, data.get('room_wxid'),
                                                                             self.from_user_id)
            else:
                raise NotImplementedError(
                    "Unsupported message type: Type:{} MsgType:{}".format(wechat_msg["type"], wechat_msg["type"]))

            if self.is_group:
                directory = os.path.join(os.getcwd(), "tmp")
                file_path = os.path.join(directory, "wx_room_members.json")
                with open(file_path, 'r', encoding='utf-8') as file:
                    room_members = json.load(file)
                self.other_user_nickname = rooms.get(data.get('room_wxid'))
                self.other_user_id = data.get('room_wxid')
                if self.from_user_id:
                    at_list = data.get('at_user_list', [])
                    self.is_at = user_id in at_list
                    content = data.get('msg', '')
                    pattern = f"@{re.escape(nickname)}(\u2005|\u0020)"
                    self.is_at |= bool(re.search(pattern, content))
                    self.actual_user_id = self.from_user_id
                    if not self.actual_user_nickname:
                        self.actual_user_nickname = get_display_name_or_nickname(room_members, data.get('room_wxid'),
                                                                                 self.from_user_id)
                else:
                    logger.error("群聊消息中没有找到 conversation_id 或 room_wxid")

            logger.debug(f"WechatMessage has been successfully instantiated with message id: {self.msg_id}")
        except Exception as e:
            logger.error(f"在 WechatMessage 的初始化过程中出现错误：{e}")
            raise e
