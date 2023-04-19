# -*- coding: utf-8 -*-
import io
import imghdr
import requests
from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel.wechatmp.wechatmp_client import WechatMPClient
from channel.wechatmp.common import *
from common.log import logger
from common.singleton import singleton
from config import conf

import web
# If using SSL, uncomment the following lines, and modify the certificate path.
# from cheroot.server import HTTPServer
# from cheroot.ssl.builtin import BuiltinSSLAdapter
# HTTPServer.ssl_adapter = BuiltinSSLAdapter(
#         certificate='/ssl/cert.pem',
#         private_key='/ssl/cert.key')


@singleton
class WechatMPChannel(ChatChannel):
    def __init__(self, passive_reply=True):
        super().__init__()
        self.passive_reply = passive_reply
        self.flag = 0

        self.client = WechatMPClient()
        if self.passive_reply:
            self.NOT_SUPPORT_REPLYTYPE = [ReplyType.IMAGE, ReplyType.VOICE]
            # Cache the reply to the user's first message
            self.cache_dict = dict()
            # Record whether the current message is being processed
            self.running = set()
            # Count the request from wechat official server by message_id
            self.request_cnt = dict()
        else:
            self.NOT_SUPPORT_REPLYTYPE = []


    def startup(self):
        if self.passive_reply:
            urls = ("/wx", "channel.wechatmp.passive_reply.Query")
        else:
            urls = ("/wx", "channel.wechatmp.active_reply.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("wechatmp_port", 8080)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))


    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if self.passive_reply:
            logger.info("[wechatmp] reply to {} cached:\n{}".format(receiver, reply))
            self.cache_dict[receiver] = reply.content
        else:
            if reply.type == ReplyType.TEXT or reply.type == ReplyType.INFO or reply.type == ReplyType.ERROR:
                reply_text = reply.content
                self.client.send_text(receiver, reply_text)
                logger.info("[wechatmp] Do send to {}: {}".format(receiver, reply_text))

            elif reply.type == ReplyType.VOICE:
                voice_file_path = reply.content
                logger.info("[wechatmp] voice file path {}".format(voice_file_path))
                with open(voice_file_path, 'rb') as f:
                    filename = receiver + "-" + context["msg"].msg_id + ".mp3"
                    media_id = self.client.upload_media("voice", (filename, f, "audio/mpeg"))
                    self.client.send_voice(receiver, media_id)
                    logger.info("[wechatmp] Do send voice to {}".format(receiver))

            elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
                img_url = reply.content
                pic_res = requests.get(img_url, stream=True)
                print(pic_res.headers)
                image_storage = io.BytesIO()
                for block in pic_res.iter_content(1024):
                    image_storage.write(block)
                image_storage.seek(0)
                image_type = imghdr.what(image_storage)
                filename = receiver + "-" + context["msg"].msg_id + "." + image_type
                content_type = "image/" + image_type
                # content_type = pic_res.headers.get('content-type')
                media_id = self.client.upload_media("image", (filename, image_storage, content_type))
                self.client.send_image(receiver, media_id)
                logger.info("[wechatmp] sendImage url={}, receiver={}".format(img_url, receiver))

            elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
                image_storage = reply.content
                image_storage.seek(0)
                image_type = imghdr.what(image_storage)
                filename = receiver + "-" + context["msg"].msg_id + "." + image_type
                content_type = "image/" + image_type
                media_id = self.client.upload_media("image", (filename, image_storage, content_type))
                self.client.send_image(receiver, media_id)
                logger.info("[wechatmp] sendImage, receiver={}".format(receiver))

        return

    def _success_callback(self, session_id, context, **kwargs):  # 线程异常结束时的回调函数
        logger.debug(
            "[wechatmp] Success to generate reply, msgId={}".format(
                context["msg"].msg_id
            )
        )
        if self.passive_reply:
            self.running.remove(session_id)

    def _fail_callback(self, session_id, exception, context, **kwargs):  # 线程异常结束时的回调函数
        logger.exception(
            "[wechatmp] Fail to generate reply to user, msgId={}, exception={}".format(
                context["msg"].msg_id, exception
            )
        )
        if self.passive_reply:
            assert session_id not in self.cache_dict
            self.running.remove(session_id)
