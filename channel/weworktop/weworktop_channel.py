import io
import random
import tempfile
import threading
import time

import requests
import uuid
from typing import Tuple
from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel.weworktop.weworktop_message import *
from channel.weworktop.weworktop_message import WeworkMessage
from common.singleton import singleton
from common.log import logger
from common.time_check import time_checker
from config import conf
from PIL import Image
from channel.weworktop.weworkapi_model import MyApiClient
from channel.weworktop.http_server import run_server, register_handler, forever
from pydub import AudioSegment

api_client = MyApiClient(base_url=conf().get("wework_http", "http://127.0.0.1:8000"))


def get_wxid_by_name(room_members, group_wxid, name):
    if group_wxid in room_members:
        for member in room_members[group_wxid]['data']['member_list']:
            if member['room_nickname'] == name or member['username'] == name:
                return member['user_id']
    return None  # 如果没有找到对应的group_wxid或name，则返回None


def download_and_compress_image(url, filename, quality=30):
    # 确定保存图片的目录
    directory = os.path.join(os.getcwd(), "tmp")
    # 如果目录不存在，则创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)
    # 下载图片
    response = requests.get(url)
    image = Image.open(io.BytesIO(response.content))
    # 压缩图片
    image_path = os.path.join(directory, f"{filename}.jpg")
    image.save(image_path, "JPEG", quality=quality)
    return image_path


def download_video(url, filename):
    # 确定保存视频的目录
    directory = os.path.join(os.getcwd(), "tmp")
    # 如果目录不存在，则创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)
    # 下载视频
    response = requests.get(url, stream=True)
    total_size = 0
    video_path = os.path.join(directory, f"{filename}.mp4")
    with open(video_path, 'wb') as f:
        for block in response.iter_content(1024):
            total_size += len(block)
            # 如果视频的总大小超过30MB (30 * 1024 * 1024 bytes)，则停止下载并返回
            if total_size > 30 * 1024 * 1024:
                logger.info("[WX] Video is larger than 30MB, skipping...")
                return None
            f.write(block)
    return video_path


def create_message(api_client, message, is_group):
    logger.debug(f"正在为{'群聊' if is_group else '单聊'}创建 WeworkMessage")
    cmsg = WeworkMessage(api_client, message, is_group=is_group)
    logger.debug(f"cmsg:{cmsg}")
    return cmsg


def handle_message(cmsg, is_group):
    logger.debug(f"准备用 WeworkTopChannel 处理{'群聊' if is_group else '单聊'}消息")
    if is_group:
        WeworkTopChannel().handle_group(cmsg)
    else:
        WeworkTopChannel().handle_single(cmsg)
    logger.debug(f"已用 WeworkTopChannel 处理完{'群聊' if is_group else '单聊'}消息")


def convert_to_silk(media_path: str) -> Tuple[str, int]:
    """将输入的媒体文件转出为 silk, 并返回silk路径"""
    output_dir = os.path.join(os.getcwd(), "tmp")
    media = AudioSegment.from_file(media_path)
    pcm_path = os.path.basename(media_path)
    pcm_path = os.path.splitext(pcm_path)[0]
    silk_path = pcm_path + '.silk'
    pcm_path += '.pcm'
    silk_path = os.path.join(output_dir, silk_path)
    pcm_path = os.path.join(output_dir, pcm_path)
    media.export(pcm_path, 's16le', parameters=['-ar', str(media.frame_rate), '-ac', '1']).close()
    pilk.encode(pcm_path, silk_path, pcm_rate=media.frame_rate, tencent=True)
    duration_ms = pilk.get_duration(silk_path)
    duration_s = int(duration_ms / 1000)
    return silk_path, duration_s


def _check(func):
    def wrapper(self, cmsg: ChatMessage):
        msgId = cmsg.msg_id
        create_time = cmsg.create_time  # 消息时间戳
        if create_time is None:
            return func(self, cmsg)
        if int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[WX]history message {} skipped".format(msgId))
            return
        return func(self, cmsg)

    return wrapper


def create_directory(directory):
    """创建目录"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_to_json(file_path, data):
    """保存数据到json文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def accept_friend_with_delay(guid, user_id, corp_id):
    # 添加随机延迟，例如在1到60秒之间
    delay = random.uniform(1, 60)
    time.sleep(delay)
    api_client.accept_friend(guid, user_id, corp_id)


@register_handler
def all_msg_handler(message):
    if message["message"]["type"] in [11041, 11044, 11042, 11043, 11045, 11047, 11072]:
        data = message['message']['data']
        conversation_id = data.get('conversation_id', data.get('room_conversation_id'))
        if conversation_id is not None:
            is_group = "R:" in conversation_id
            try:
                cmsg = create_message(api_client, message=message, is_group=is_group)
            except NotImplementedError as e:
                logger.error(f"[WX]{data.get('conversation_id', 'unknown')} 跳过: {e}")
                return
            handle_message(cmsg, is_group)
            return
        else:
            logger.debug("消息数据中无 conversation_id")
            return
    elif message["message"]["type"] == 11063:
        accept_friend = conf().get('accept_friend', False)
        if accept_friend:
            guid = message["guid"]
            user_id = message["message"]["data"]["user_id"]
            corp_id = message["message"]["data"]["corp_id"]

            # 创建一个新线程来异步执行 accept_friend_with_delay 函数
            thread = threading.Thread(target=accept_friend_with_delay, args=(guid, user_id, corp_id))
            thread.daemon = True
            thread.start()
            return
        else:
            return
    else:
        return


@singleton
class WeworkTopChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.guid = None
        self.login_info = None

    def startup(self):
        try:
            # 在新线程中运行服务器
            wework_callback_port = conf().get("wework_callback_port", 8001)
            server_thread = threading.Thread(target=run_server, args=(wework_callback_port,))
            server_thread.daemon = True
            server_thread.start()
            callback_url = f"http://127.0.0.1:{wework_callback_port}"
            logger.debug(f"callback_url :{callback_url}")
            callback_url_response = api_client.client_set_callback_url(callback_url)
            self.guid = callback_url_response['data']['guid']
            if not self.guid:
                raise Exception("启动失败，guid为空")
            logger.debug(f"wework guid:{self.guid}")
            time.sleep(5)
            response = api_client.user_get_profile(self.guid)
            logger.debug(f"user_get_profile response:{response}")
            self.login_info = response['data']
            self.user_id = self.login_info['user_id']
            self.name = self.login_info['nickname'] if self.login_info['nickname'] else self.login_info['username']
            logger.info(f"登录信息:>>>user_id:{self.user_id}>>>>>>>>name:{self.name}")

            contacts, rooms = api_client.get_external_contacts(self.guid, 1, 50000), api_client.get_rooms(self.guid)
            logger.debug(f"获取到的群聊信息： \n {rooms}")
            if not contacts or not rooms:
                raise Exception("获取contacts或rooms失败")

            directory = os.path.join(os.getcwd(), "tmp")
            create_directory(directory)

            save_to_json(os.path.join(directory, 'wework_contacts.json'), contacts)
            save_to_json(os.path.join(directory, 'wework_rooms.json'), rooms)

            # 创建一个空字典来保存结果
            result = {}
            rooms_data = rooms['data']['room_list']

            # 遍历列表中的每个字典
            for room in rooms_data:
                # 获取聊天室ID
                room_wxid = room['conversation_id']

                # 获取聊天室成员
                room_members = api_client.get_room_members(self.guid, room_wxid, 1, 500)

                # 将聊天室成员保存到结果字典中
                result[room_wxid] = room_members

            save_to_json(os.path.join(directory, 'wework_room_members.json'), result)

            logger.info("wework程序初始化完成········")
            forever()
        except Exception as e:
            logger.error(str(e))
            return

    @time_checker
    @_check
    def handle_single(self, cmsg: ChatMessage):
        if cmsg.ctype == ContextType.VOICE:
            if not conf().get("speech_recognition"):
                return
            logger.debug("[WX]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[WX]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[WX]receive text msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
        elif cmsg.ctype == ContextType.FILE:
            logger.debug("[WX]receive file msg: {}".format(cmsg.content))
        else:
            logger.debug("[WX]receive msg: {}, cmsg={}".format(cmsg.content, cmsg))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        if context:
            self.produce(context)

    @time_checker
    @_check
    def handle_group(self, cmsg: ChatMessage):
        if cmsg.ctype == ContextType.VOICE:
            if not conf().get("speech_recognition"):
                return
            logger.debug("[WX]receive voice for group msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image for group msg: {}".format(cmsg.content))
        elif cmsg.ctype in [ContextType.JOIN_GROUP, ContextType.PATPAT]:
            logger.debug("[WX]receive note msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            pass
        elif cmsg.ctype == ContextType.FILE:
            logger.debug("[WX]receive file msg: {}".format(cmsg.content))
        else:
            logger.debug("[WX]receive group msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        session_id = context["session_id"]
        if reply.type == ReplyType.TEXT or reply.type == ReplyType.TEXT_:
            match = re.search(r"^@(.*?)\n", reply.content)
            if match:
                new_content = re.sub(r"^@(.*?)\n", "\n", reply.content)
                wxid_list = [session_id]
                api_client.send_room_at(self.guid, receiver, new_content, wxid_list)
            else:
                api_client.msg_send_text(self.guid, receiver, reply.content)
                logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
            api_client.msg_send_text(self.guid, receiver, reply.content)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            image_storage = reply.content
            image_storage.seek(0)
            # Read data from image_storage
            data = image_storage.read()
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp_path = temp.name
                temp.write(data)
            # Send the image
            api_client.send_image(self.guid, receiver, temp_path)
            logger.info("[WX] sendImage, receiver={}".format(receiver))
            # Remove the temporary file
            os.remove(temp_path)
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            filename = str(uuid.uuid4())
            image_path = download_and_compress_image(img_url, filename)
            api_client.send_image(self.guid, receiver, image_path)
            logger.info("[WX] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.VIDEO_URL:
            video_url = reply.content
            filename = str(uuid.uuid4())
            video_path = download_video(video_url, filename)
            if video_path is None:
                # 如果视频太大，下载可能会被跳过，此时 video_path 将为 None
                api_client.msg_send_text(self.guid, receiver, "抱歉，视频太大了！！！")
            else:
                api_client.send_video(self.guid, receiver, video_path)
            logger.info("[WX] sendVideo, receiver={}".format(receiver))
        elif reply.type == ReplyType.VIDEO:
            api_client.send_video(self.guid, receiver, reply.content)
            logger.info("[WX] sendVideo, receiver={}".format(receiver))
        elif reply.type == ReplyType.VOICE:
            directory = os.path.join(os.getcwd(), "tmp")
            filename = os.path.basename(reply.content)
            wav_path = os.path.join(directory, filename)
            silk_path, duration_s = convert_to_silk(wav_path)
            file_path = os.path.join(directory, silk_path)
            data_ = api_client.cdn_upload(self.guid, file_path, 5)
            logger.debug(f"data_:{data_}")
            data = data_.get('data')
            if not data:
                api_client.send_file(self.guid, receiver, wav_path)
                logger.info("[WX] sendVoice, receiver={}".format(receiver))
            elif duration_s > 60:
                api_client.send_file(self.guid, receiver, wav_path)
                logger.info("[WX] sendVoice, receiver={}".format(receiver))
            else:
                api_client.send_voice(self.guid, receiver, data.get('file_id'), data.get('file_size'), duration_s,
                                      data.get('file_aes_key'), data.get('file_md5'))
                logger.info("[WX] sendVoice, receiver={}".format(receiver))
        elif reply.type == ReplyType.CARD:
            api_client.send_card(self.guid, receiver, reply.content)
        elif reply.type == ReplyType.FILE:
            api_client.send_file(self.guid, receiver, reply.content)
        elif reply.type == ReplyType.InviteRoom:
            receiver_id = receiver.split("_")[-1]
            member_list = [receiver_id]
            api_client.invite_to_room(self.guid, member_list, reply.content)
            logger.info("[WX] sendInviteRoom={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.MINIAPP:
            logger.debug(reply.content)
            aes_key = reply.content["aes_key"]
            file_id = reply.content["file_id"]
            size = reply.content["size"]
            appicon = reply.content["appicon"]
            appid = reply.content["appid"]
            appname = reply.content["appname"]
            page_path = reply.content["page_path"]
            title = reply.content["title"]
            username = reply.content["username"]
            api_client.send_miniapp(self.guid, receiver, aes_key, file_id, size, appicon, appid, appname, page_path,
                                    title, username)
            logger.info("[WX] sendInviteRoom={}, receiver={}".format(reply.content, receiver))
