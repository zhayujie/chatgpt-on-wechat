import datetime
import json
import os
import re
import pilk

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from config import conf

LOGIN_INFO_CACHE = {}


def get_room_info(conversation_id):
    directory = os.path.join(os.getcwd(), "tmp")
    file_path = os.path.join(directory, "wework_rooms.json")
    logger.debug(f"传入的 conversation_id: {conversation_id}")

    # 从文件中读取群聊信息
    with open(file_path, 'r', encoding='utf-8') as file:
        rooms_data = json.load(file)

    if 'data' not in rooms_data or 'room_list' not in rooms_data['data']:
        logger.error(f"获取群聊信息失败: {rooms_data}")
        return None

    rooms = rooms_data['data']['room_list']

    logger.debug(f"获取到的群聊信息: {rooms}")
    for room in rooms:
        if room['conversation_id'] == conversation_id:
            return room
    return None


def cdn_download(guid, api_client, data, file_name):
    url = data["cdn"]["url"]
    auth_key = data["cdn"]["auth_key"]
    aes_key = data["cdn"]["aes_key"]
    file_size = data["cdn"]["size"]

    # 获取当前工作目录，然后与文件名拼接得到保存路径
    current_dir = os.getcwd()
    save_path = os.path.join(current_dir, "tmp", file_name)

    result = api_client.wx_cdn_download(guid, url, auth_key, aes_key, file_size, save_path)
    logger.debug(result)


def c2c_download_and_convert(guid, api_client, data, file_name):
    aes_key = data["cdn"]["aes_key"]
    file_size = data["cdn"]["size"]
    file_type = 5
    file_id = data["cdn"]["file_id"]

    current_dir = os.getcwd()
    save_path = os.path.join(current_dir, "tmp", file_name)
    result = api_client.c2c_cdn_download(guid, file_id, aes_key, file_size, file_type, save_path)
    logger.debug(result)

    # 在下载完SILK文件之后，立即将其转换为WAV文件
    base_name, _ = os.path.splitext(save_path)
    wav_file = base_name + ".wav"
    pilk.silk_to_wav(save_path, wav_file, rate=24000)


class WeworkMessage(ChatMessage):
    def __init__(self, api_client, message, is_group=False):
        try:
            super().__init__(message)
            data = message['message']['data']
            logger.debug(f"message data:{data}")
            guid = message['guid']
            logger.debug(f"message type：{message['message']['type']}   message guid:{guid}")
            message = message['message']
            self.msg_id = data.get('conversation_id', data.get('room_conversation_id'))
            # 使用.get()防止 'send_time' 键不存在时抛出错误
            self.create_time = data.get("send_time")
            self.is_group = is_group
            self.api_client = api_client

            # 检查是否已经缓存了该 guid 的 login_info_
            if guid not in LOGIN_INFO_CACHE:
                LOGIN_INFO_CACHE[guid] = self.api_client.user_get_profile(guid)

            self.login_info_ = LOGIN_INFO_CACHE[guid]

            if message["type"] == 11041:  # 文本消息类型
                if any(substring in data['content'] for substring in ("该消息类型暂不能展示", "不支持的消息类型")):
                    return
                self.ctype = ContextType.TEXT
                self.content = message['data']['content']
            elif message["type"] == 11044:  # 语音消息类型，需要缓存文件
                file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".silk"
                base_name, _ = os.path.splitext(file_name)
                file_name_2 = base_name + ".wav"
                current_dir = os.getcwd()
                self.ctype = ContextType.VOICE
                self.content = os.path.join(current_dir, "tmp", file_name_2)
                self._prepare_fn = lambda: c2c_download_and_convert(guid, self.api_client, data, file_name)
            elif message["type"] == 11042:  # 图片消息类型，需要下载文件
                file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".jpg"
                current_dir = os.getcwd()
                self.ctype = ContextType.IMAGE
                self.content = os.path.join(current_dir, "tmp", file_name)
                self._prepare_fn = lambda: cdn_download(guid, self.api_client, data, file_name)
            elif message["type"] == 11045:  # 文件消息类型，需要下载文件
                file_name = data["cdn"]["file_name"]
                current_dir = os.getcwd()
                self.ctype = ContextType.FILE
                self.content = os.path.join(current_dir, "tmp", file_name)
                self._prepare_fn = lambda: cdn_download(guid, self.api_client, data, file_name)
            elif message["type"] == 11043:  # 视频消息类型，需要下载文件
                file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".mp4"
                current_dir = os.getcwd()
                self.ctype = ContextType.VIDEO
                self.content = os.path.join(current_dir, "tmp", file_name)
                self._prepare_fn = lambda: cdn_download(guid, self.api_client, data, file_name)
            elif message["type"] == 11072:  # 新成员入群通知
                self.ctype = ContextType.JOIN_GROUP
                member_list = message['data']['member_list']
                self.actual_user_nickname = member_list[0]['name']
                self.actual_user_id = member_list[0]['user_id']
                self.content = f"{self.actual_user_nickname}加入了群聊！"
                directory = os.path.join(os.getcwd(), "tmp")
                rooms = self.api_client.get_rooms(guid)
                if not rooms:
                    logger.error("更新群信息失败···")
                else:
                    result = {}
                    rooms_data = rooms['data']['room_list']
                    for room in rooms_data:
                        # 获取聊天室ID
                        room_wxid = room['conversation_id']

                        # 获取聊天室成员
                        room_members = self.api_client.get_room_members(guid, room_wxid, 1, 500)

                        # 将聊天室成员保存到结果字典中
                        result[room_wxid] = room_members
                    with open(os.path.join(directory, 'wework_room_members.json'), 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=4)
                    logger.info("有新成员加入，已自动更新群成员列表缓存！")
            elif message["type"] == 11047:  # 链接分享通知
                self.ctype = ContextType.TEXT
                if self.is_group:
                    group_chat_prefix = conf().get("group_chat_prefix")
                    first_value = group_chat_prefix[0] if group_chat_prefix else ""
                    self.content = first_value + "访问链接：" + message['data']['url']
                else:
                    self.content = "访问链接：" + message['data']['url']
            else:
                raise NotImplementedError(
                    "Unsupported message type: guid:{} MsgType:{}".format(guid, message["type"]))

            login_info = self.login_info_['data']
            nickname = login_info['nickname'] if login_info['nickname'] else login_info['username']
            user_id = login_info['user_id']

            sender_id = data.get('sender')
            conversation_id = data.get('conversation_id')
            sender_name = data.get("sender_name")

            self.from_user_id = user_id if sender_id == user_id else sender_id
            self.from_user_nickname = nickname if sender_id == user_id else sender_name
            self.to_user_id = user_id
            self.to_user_nickname = nickname
            self.other_user_nickname = sender_name
            self.other_user_id = conversation_id

            if self.is_group:
                conversation_id = data.get('conversation_id') or data.get('room_conversation_id')
                self.other_user_id = conversation_id
                if conversation_id:
                    room_info = get_room_info(conversation_id)
                    self.other_user_nickname = room_info.get('nickname', None) if room_info else None
                    at_list = data.get('at_list', [])
                    self.is_at = nickname in at_list

                    # 检查消息内容是否包含@用户名。处理复制粘贴的消息，这类消息可能不会触发@通知，但内容中可能包含 "@用户名"。
                    content = data.get('content', '')
                    name = nickname
                    pattern = f"@{re.escape(name)}(\u2005|\u0020)"
                    if re.search(pattern, content):
                        logger.debug(f"Wechaty message {self.msg_id} includes at")
                        self.is_at = True

                    if not self.actual_user_id:
                        self.actual_user_id = data.get("sender")
                    self.actual_user_nickname = sender_name if self.ctype != ContextType.JOIN_GROUP else self.actual_user_nickname
                else:
                    logger.error("群聊消息中没有找到 conversation_id 或 room_conversation_id")

            logger.debug(f"WeworkMessage has been successfully instantiated with message id: {self.msg_id}")
        except Exception as e:
            logger.error(f"在 WeworkMessage 的初始化过程中出现错误：{e}")
            raise e
