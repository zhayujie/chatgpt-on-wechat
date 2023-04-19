#!/usr/bin/env python
# -*- coding=utf-8 -*-
import io
import os
import textwrap

import requests
import web
from wechatpy.enterprise import WeChatClient, create_reply, parse_message
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.enterprise.exceptions import InvalidCorpIdException
from wechatpy.exceptions import InvalidSignatureException, WeChatClientException

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.wechatcom.wechatcom_message import WechatComMessage
from common.log import logger
from common.singleton import singleton
from config import conf
from voice.audio_convert import any_to_amr


@singleton
class WechatComChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.corp_id = conf().get("wechatcom_corp_id")
        self.secret = conf().get("wechatcom_secret")
        self.agent_id = conf().get("wechatcom_agent_id")
        self.token = conf().get("wechatcom_token")
        self.aes_key = conf().get("wechatcom_aes_key")
        print(self.corp_id, self.secret, self.agent_id, self.token, self.aes_key)
        logger.info(
            "[wechatcom] init: corp_id: {}, secret: {}, agent_id: {}, token: {}, aes_key: {}".format(
                self.corp_id, self.secret, self.agent_id, self.token, self.aes_key
            )
        )
        self.crypto = WeChatCrypto(self.token, self.aes_key, self.corp_id)
        self.client = WeChatClient(self.corp_id, self.secret)  # todo: 这里可能有线程安全问题

    def startup(self):
        # start message listener
        urls = ("/wxcom", "channel.wechatcom.wechatcom_channel.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("wechatcom_port", 8080)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            self.client.message.send_text(self.agent_id, receiver, reply.content)
            logger.info("[wechatcom] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.VOICE:
            try:
                file_path = reply.content
                amr_file = os.path.splitext(file_path)[0] + ".amr"
                any_to_amr(file_path, amr_file)
                response = self.client.media.upload("voice", open(amr_file, "rb"))
                logger.debug("[wechatcom] upload voice response: {}".format(response))
            except WeChatClientException as e:
                logger.error("[wechatcom] upload voice failed: {}".format(e))
                return
            try:
                os.remove(file_path)
                if amr_file != file_path:
                    os.remove(amr_file)
            except Exception:
                pass
            self.client.message.send_voice(
                self.agent_id, receiver, response["media_id"]
            )
            logger.info(
                "[wechatcom] sendVoice={}, receiver={}".format(reply.content, receiver)
            )
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)
            try:
                response = self.client.media.upload("image", image_storage)
                logger.debug("[wechatcom] upload image response: {}".format(response))
            except WeChatClientException as e:
                logger.error("[wechatcom] upload image failed: {}".format(e))
                return
            self.client.message.send_image(
                self.agent_id, receiver, response["media_id"]
            )
            logger.info(
                "[wechatcom] sendImage url={}, receiver={}".format(img_url, receiver)
            )
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            image_storage = reply.content
            image_storage.seek(0)
            try:
                response = self.client.media.upload("image", image_storage)
                logger.debug("[wechatcom] upload image response: {}".format(response))
            except WeChatClientException as e:
                logger.error("[wechatcom] upload image failed: {}".format(e))
                return
            self.client.message.send_image(
                self.agent_id, receiver, response["media_id"]
            )
            logger.info("[wechatcom] sendImage, receiver={}".format(receiver))


class Query:
    def GET(self):
        channel = WechatComChannel()
        params = web.input()
        signature = params.msg_signature
        timestamp = params.timestamp
        nonce = params.nonce
        echostr = params.echostr
        print(params)
        try:
            echostr = channel.crypto.check_signature(
                signature, timestamp, nonce, echostr
            )
        except InvalidSignatureException:
            raise web.Forbidden()
        return echostr

    def POST(self):
        channel = WechatComChannel()
        params = web.input()
        signature = params.msg_signature
        timestamp = params.timestamp
        nonce = params.nonce
        try:
            message = channel.crypto.decrypt_message(
                web.data(), signature, timestamp, nonce
            )
        except (InvalidSignatureException, InvalidCorpIdException):
            raise web.Forbidden()
        msg = parse_message(message)
        logger.debug("[wechatcom] receive message: {}, msg= {}".format(message, msg))
        if msg.type == "event":
            if msg.event == "subscribe":
                trigger_prefix = conf().get("single_chat_prefix", [""])[0]
                reply_content = textwrap.dedent(
                    f"""\
                    感谢您的关注！
                    这里是ChatGPT，可以自由对话。
                    支持语音对话。
                    支持通用表情输入。
                    支持图片输入输出。
                    支持角色扮演和文字冒险两种定制模式对话。
                    输入'{trigger_prefix}#help' 查看详细指令。"""
                )
                reply = create_reply(reply_content, msg).render()
                res = channel.crypto.encrypt_message(reply, nonce, timestamp)
                return res
        else:
            try:
                wechatcom_msg = WechatComMessage(msg, client=channel.client)
            except NotImplementedError as e:
                logger.debug("[wechatcom] " + str(e))
                return "success"
            context = channel._compose_context(
                wechatcom_msg.ctype,
                wechatcom_msg.content,
                isgroup=False,
                msg=wechatcom_msg,
            )
            if context:
                channel.produce(context)
        return "success"
