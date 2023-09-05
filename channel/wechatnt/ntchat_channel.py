import io
import random
import threading
import uuid
import xml.dom.minidom
import requests

from PIL import Image
from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel.wechatnt.ntchat_message import *
from common.singleton import singleton
from common.log import logger
from common.time_check import time_checker
from config import conf
from channel.wechatnt.nt_run import *


def download_and_compress_image(url, filename, quality=80):
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


def get_wxid_by_name(room_members, group_wxid, name):
    if group_wxid in room_members:
        for member in room_members[group_wxid]['member_list']:
            if member['display_name'] == name or member['nickname'] == name:
                return member['wxid']
    return None  # 如果没有找到对应的group_wxid或name，则返回None


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


# 注册消息回调
@wechatnt.msg_register([ntchat.MT_RECV_TEXT_MSG, ntchat.MT_RECV_IMAGE_MSG,
                        ntchat.MT_RECV_VOICE_MSG, ntchat.MT_ROOM_ADD_MEMBER_NOTIFY_MSG,
                        ntchat.MT_RECV_SYSTEM_MSG])
def all_msg_handler(wechat_instance: ntchat.WeChat, message):
    logger.debug(f"收到消息: {message}")
    if message["data"]["room_wxid"]:
        try:
            cmsg = NtchatMessage(wechat_instance, message, True)
            ifgroup = True
        except NotImplementedError as e:
            logger.debug("[WX]single message {} skipped: {}".format(message["MsgId"], e))
            return None
    else:
        try:
            cmsg = NtchatMessage(wechat_instance, message, False)
            ifgroup = False
        except NotImplementedError as e:
            logger.debug("[WX]single message {} skipped: {}".format(message["MsgId"], e))
            return None

    if ifgroup:
        NtchatChannel().handle_group(cmsg)
    else:
        NtchatChannel().handle_single(cmsg)
    logger.debug(f"cmsg: {cmsg}")
    return None


# 注册好友请求监听
@wechatnt.msg_register(ntchat.MT_RECV_FRIEND_MSG)
def on_recv_text_msg(wechat_instance: ntchat.WeChat, message):
    xml_content = message["data"]["raw_msg"]
    dom = xml.dom.minidom.parseString(xml_content)

    # 从xml取相关参数
    encryptusername = dom.documentElement.getAttribute("encryptusername")
    ticket = dom.documentElement.getAttribute("ticket")
    scene = dom.documentElement.getAttribute("scene")

    if conf().get("accept_friend", False):
        # 自动同意好友申请
        delay = random.randint(1, 180)
        threading.Timer(delay, wechat_instance.accept_friend_request,
                        args=(encryptusername, ticket, int(scene))).start()
    else:
        logger.debug("ntchat未开启自动同意好友申请")


@singleton
class NtchatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()

    def startup(self):
        smart = conf().get("ntchat_smart", True)
        wechatnt.open(smart=smart)
        wechatnt.wait_login()
        logger.info("等待登录······")
        login_info = wechatnt.get_login_info()
        contacts = wechatnt.get_contacts()
        directory = os.path.join(os.getcwd(), "tmp")
        rooms = wechatnt.get_rooms()
        if not os.path.exists(directory):
            os.makedirs(directory)
        # 将contacts保存到json文件中
        with open(os.path.join(directory, 'wx_contacts.json'), 'w', encoding='utf-8') as f:
            json.dump(contacts, f, ensure_ascii=False, indent=4)
        with open(os.path.join(directory, 'wx_rooms.json'), 'w', encoding='utf-8') as f:
            json.dump(rooms, f, ensure_ascii=False, indent=4)
        # 创建一个空字典来保存结果
        result = {}

        # 遍历列表中的每个字典
        for room in rooms:
            # 获取聊天室ID
            room_wxid = room['wxid']

            # 获取聊天室成员
            room_members = wechatnt.get_room_members(room_wxid)

            # 将聊天室成员保存到结果字典中
            result[room_wxid] = room_members

        # 将结果保存到json文件中
        with open(os.path.join(directory, 'wx_room_members.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        self.user_id = login_info['wxid']
        self.name = login_info['nickname']
        logger.info(f"登录信息:>>>user_id:{self.user_id}>>>>>>>>name:{self.name}")
        forever()

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
            # logger.debug("[WX]receive group msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
            pass
        else:
            logger.debug("[WX]receive group msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type == ReplyType.TEXT or reply.type == ReplyType.TEXT_:
            match = re.search(r"^@(.*?)\n", reply.content)
            if match:
                name = match.group(1)  # 获取第一个组的内容，即名字
                directory = os.path.join(os.getcwd(), "tmp")
                file_path = os.path.join(directory, "wx_room_members.json")
                with open(file_path, 'r', encoding='utf-8') as file:
                    room_members = json.load(file)
                wxid = get_wxid_by_name(room_members, receiver, name)
                wxid_list = [wxid]
                wechatnt.send_room_at_msg(receiver, reply.content, wxid_list)
            else:
                wechatnt.send_text(receiver, reply.content)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
            wechatnt.send_text(receiver, reply.content)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            filename = str(uuid.uuid4())
            image_path = download_and_compress_image(img_url, filename)
            wechatnt.send_image(receiver, file_path=image_path)
            logger.info("[WX] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            wechatnt.send_image(reply.content, toUserName=receiver)
            logger.info("[WX] sendImage, receiver={}".format(receiver))
        elif reply.type == ReplyType.VIDEO_URL:
            video_url = reply.content
            filename = str(uuid.uuid4())
            # 调用你的函数，下载视频并保存为本地文件
            video_path = download_video(video_url, filename)
            if video_path is None:
                # 如果视频太大，下载可能会被跳过，此时 video_path 将为 None
                wechatnt.send_text(receiver, "抱歉，视频太大了！！！")
            else:
                wechatnt.send_video(receiver, video_path)
            logger.info("[WX] sendVideo, receiver={}".format(receiver))
        elif reply.type == ReplyType.CARD:
            wechatnt.send_card(receiver, reply.content)
            logger.info("[WX] sendCARD={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.InviteRoom:
            member_list = [receiver]
            wechatnt.invite_room_member(reply.content, member_list)
            logger.info("[WX] sendInviteRoom={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.VOICE:
            wechatnt.send_file(receiver, reply.content)
            logger.info("[WX] sendFile={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.MINIAPP:
            wechatnt.send_xml(receiver, reply.content)
            logger.info("[WX] sendFile={}, receiver={}".format(reply.content, receiver))
