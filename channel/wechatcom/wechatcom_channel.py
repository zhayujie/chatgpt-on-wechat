#!/usr/bin/env python
# -*- coding=utf-8 -*-
import web
from wechatpy.enterprise import WeChatClient, create_reply, parse_message
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.enterprise.exceptions import InvalidCorpIdException
from wechatpy.exceptions import InvalidSignatureException

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.wechatcom.wechatcom_message import WechatComMessage
from common.log import logger
from common.singleton import singleton
from config import conf


@singleton
class WechatComChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = [ReplyType.IMAGE, ReplyType.VOICE]

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
        print("send reply: ", reply.content, context["receiver"])
        receiver = context["receiver"]
        reply_text = reply.content
        self.client.message.send_text(self.agent_id, receiver, reply_text)
        logger.info("[send] Do send to {}: {}".format(receiver, reply_text))


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
        print(message)
        msg = parse_message(message)

        print(msg)
        if msg.type == "event":
            if msg.event == "subscribe":
                reply = create_reply("感谢关注", msg).render()
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
