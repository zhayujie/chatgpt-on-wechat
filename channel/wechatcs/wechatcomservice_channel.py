# -*- coding=utf-8 -*-
import io
import json
import os
import time

import requests
import web
from wechatpy.enterprise import create_reply, parse_message
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.enterprise.exceptions import InvalidCorpIdException
from wechatpy.exceptions import InvalidSignatureException, WeChatClientException

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.wechatcom.wechatcomapp_client import WechatComAppClient
from channel.wechatcs.wechatcomservice_message import WechatComServiceMessage
from common.log import logger
from common.singleton import singleton
from common.utils import compress_imgfile, fsize, split_string_by_utf8_length
from config import conf, subscribe_msg
from voice.audio_convert import any_to_amr, split_audio

import web
import json
import requests
import xml.etree.ElementTree as ET
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise.exceptions import InvalidCorpIdException

MAX_UTF8_LEN = 2048


@singleton
class WechatComServiceChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.corp_id = conf().get("wechatcom_corp_id")
        self.secret = conf().get("wechatcomapp_secret")
        self.agent_id = conf().get("wechatcomapp_agent_id")
        self.token = conf().get("wechatcomapp_token")
        self.aes_key = conf().get("wechatcomapp_aes_key")
        print(self.corp_id, self.secret, self.agent_id, self.token, self.aes_key)
        logger.info(
            "[wechatcs] init: corp_id: {}, secret: {}, agent_id: {}, token: {}, aes_key: {}".format(self.corp_id,
                                                                                                    self.secret,
                                                                                                    self.agent_id,
                                                                                                    self.token,
                                                                                                    self.aes_key)
        )
        self.crypto = WeChatCrypto(self.token, self.aes_key, self.corp_id)
        self.client = WechatComAppClient(self.corp_id, self.secret)

    def startup(self):
        # start message listener
        # wechatcomservice_channel.py
        urls = ("/wxcomapp", "channel.wechatcs.wechatcomservice_channel.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("wechatcomapp_port", 9898)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        external_userid = context.kwargs['msg'].external_userid  # from_user_id
        open_kfid = context.kwargs['msg'].open_kfid  # to_user_id,也就是客服id

        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = reply.content
            texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)
            if len(texts) > 1:
                logger.info("[wechatcs] text too long, split into {} parts".format(len(texts)))
            # self.send_text_message(external_userid, open_kfid,
            #                        content, msgid=None)
            content = reply.content
            self.send_text_message(external_userid=external_userid, open_kfid=open_kfid, content=content)
            logger.info("[wechatcs] Do send text to {}: {}".format(receiver, reply_text))
        elif reply.type == ReplyType.VOICE:
            try:
                media_ids = []
                file_path = reply.content
                amr_file = os.path.splitext(file_path)[0] + ".amr"
                any_to_amr(file_path, amr_file)
                duration, files = split_audio(amr_file, 60 * 1000)
                if len(files) > 1:
                    logger.info(
                        "[wechatcs] voice too long {}s > 60s , split into {} parts".format(duration / 1000.0,
                                                                                           len(files)))
                for path in files:
                    response = self.client.media.upload("voice", open(path, "rb"))
                    logger.debug("[wechatcs] upload voice response: {}".format(response))
                    media_ids.append(response["media_id"])
            except WeChatClientException as e:
                logger.error("[wechatcs] upload voice failed: {}".format(e))
                return
            try:
                os.remove(file_path)
                if amr_file != file_path:
                    os.remove(amr_file)
            except Exception:
                pass
            for media_id in media_ids:
                # self.client.message.send_voice(self.agent_id, receiver, media_id)
                self.send_voice_message(external_userid=external_userid, open_kfid=open_kfid,
                                        media_id=media_id)
                time.sleep(1)
            logger.info("[wechatcs] sendVoice={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[wechatcs] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[wechatcs] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            try:
                response = self.client.media.upload("image", image_storage)
                logger.debug("[wechatcs] upload image response: {}".format(response))
            except WeChatClientException as e:
                logger.error("[wechatcs] upload image failed: {}".format(e))
                return

            # self.client.message.send_image(self.agent_id, receiver, response["media_id"])
            self.send_image_message(external_userid=external_userid, open_kfid=open_kfid, media_id=response["media_id"])
            logger.info("[wechatcs] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            image_storage = reply.content
            sz = fsize(image_storage)

            if sz >= 10 * 1024 * 1024:
                logger.info("[wechatcs] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[wechatcs] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            try:
                response = self.client.media.upload("image", image_storage)
                logger.debug("[wechatcs] upload image response: {}".format(response))
            except WeChatClientException as e:
                logger.error("[wechatcs] upload image failed: {}".format(e))
                return
            # self.client.message.send_image(self.agent_id, receiver, response["media_id"])
            self.send_image_message(external_userid=external_userid, open_kfid=open_kfid, media_id=response["media_id"])
            logger.info("[wechatcs] sendImage, receiver={}".format(receiver))
        elif reply.type == ReplyType.LINK:
            # 解析 reply.content 中的 JSON 数据
            try:
                # link_data = json.loads(reply.content)
                link_data = reply.content
                image_storage = link_data["image"]
                sz = fsize(image_storage)

                if sz >= 10 * 1024 * 1024:
                    logger.info("[wechatcs] image too large, ready to compress, sz={}".format(sz))
                    image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                    logger.info("[wechatcs] image compressed, sz={}".format(fsize(image_storage)))
                image_storage.seek(0)
                try:
                    response = self.client.media.upload("image", image_storage)
                    logger.debug("[wechatcs] upload image response: {}".format(response))
                except WeChatClientException as e:
                    logger.error("[wechatcs] upload image failed: {}".format(e))
                    return
                link_data["thumb_media_id"] = response["media_id"]
                # 此时已经不需要图片数据了
                link_data.pop("image")
                self.send_link_message(
                    external_userid=external_userid, open_kfid=open_kfid, link_data=link_data
                )
                logger.info("[WX] sendLinkCard, receiver={}".format(receiver))
            except json.JSONDecodeError:
                logger.error("Invalid JSON format in reply.content")

    def send_text_message(self, external_userid, open_kfid, content, msgid=None):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token={self.client.fetch_access_token()}"
        data = {
            "touser": external_userid,
            "open_kfid": open_kfid,
            "msgtype": "text",
            "text": {"content": content}
        }
        if msgid:
            data["msgid"] = msgid

        response = requests.post(url, json=data)
        return response.json()

    def send_image_message(self, external_userid, open_kfid, msgid=None, media_id=None):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token={self.client.fetch_access_token()}"
        data = {
            "touser": external_userid,
            "open_kfid": open_kfid,
            "msgtype": "image",
            "image": {"media_id": media_id}
        }
        if msgid:
            data["msgid"] = msgid

        response = requests.post(url, json=data).json()
        if response['errmsg'] == 'ok':
            print(f"Send IMAGE Message Success")
        else:
            print(f"Something error:{response}")
        return response

    def send_voice_message(self, external_userid, open_kfid, media_id, msgid=None):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token={self.client.fetch_access_token()}"
        data = {
            "touser": external_userid,
            "open_kfid": open_kfid,
            "msgtype": "voice",
            "voice": {"media_id": media_id}
        }
        if msgid:
            data["msgid"] = msgid

        response = requests.post(url, json=data).json()
        if response['errmsg'] == 'ok':
            print(f"Send VOICE Message Success")
        else:
            print(f"Something error:{response}")
        return response

    def send_link_message(self, external_userid, open_kfid, link_data, msgid=None):
        # 从 link_data 中提取信息
        # 构造发送图文链接消息的数据
        data = {
            "touser": external_userid,
            "open_kfid": open_kfid,
            "msgtype": "link",
            "link": link_data
        }
        if msgid:
            data["msgid"] = msgid
        # 发送图文链接消息
        url = f"https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token={self.client.fetch_access_token()}"
        response = requests.post(url, json=data).json()
        if response['errmsg'] == 'ok':
            print("Send LINK Message Success")
        else:
            print(f"Something error: {response}")
        return response

    def get_latest_message(self, token, open_kfid, next_cursor=""):
        logger.debug(f"self.client.fetch_access_token():{self.client.fetch_access_token()}")
        url = f"https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg?access_token={self.client.fetch_access_token()}"
        data = {
            "token": token,
            "open_kfid": open_kfid,
            "limit": 1000
        }
        if next_cursor:
            data["cursor"] = next_cursor

        response = requests.post(url, json=data)
        response_data = response.json()
        # if response_data["errcode"] == 0 and response_data["msg_list"]:
        #     return response_data["msg_list"][-1]  # 返回最新的一条消息
        # else:
        #     return None

        # 检查是否有错误码并打印相关错误信息
        if response_data.get("errcode") != 0:
            logger.error(
                f"[ERROR][{response_data.get('errcode')}][{response_data.get('errmsg')}] - Failed to fetch messages, more info at {response_data.get('more_info') or 'https://open.work.weixin.qq.com/devtool/query?e=' + str(response_data.get('errcode'))}")
            return None

        logger.debug(f"response_data:{response_data}")
        if response_data.get("msg_list"):
            return response_data["msg_list"][-1]  # 返回最新的一条消息
        else:
            return None


class Query:
    def GET(self):
        channel = WechatComServiceChannel()
        params = web.input()
        logger.info("[wechatcom] receive GET params: {}".format(params))
        try:
            signature = params.msg_signature
            timestamp = params.timestamp
            nonce = params.nonce
            echostr = params.echostr
            echostr = channel.crypto.check_signature(signature, timestamp, nonce, echostr)
        except InvalidSignatureException:
            logger.error("[wechatcs] Invalid signature in GET request")
            raise web.Forbidden()
        return echostr

    def POST(self):
        channel = WechatComServiceChannel()
        params = web.input()
        raw_data = web.data()
        logger.debug("[wechatcs] receive POST params: {}".format(params))
        logger.debug("[wechatcs] raw data: {}".format(raw_data))

        try:
            signature = params.msg_signature
            timestamp = params.timestamp
            nonce = params.nonce
            encrypted_message = channel.crypto.decrypt_message(raw_data, signature, timestamp, nonce)

            # 解析XML格式的消息
            xml_tree = ET.fromstring(encrypted_message)
            msg_type = xml_tree.find("MsgType").text
            event = xml_tree.find("Event").text if xml_tree.find("Event") is not None else ""

            if msg_type == "event" and event == "kf_msg_or_event":
                # 在这里处理特定事件
                # 示例代码，根据实际情况修改
                token = xml_tree.find("Token").text
                open_kfid = xml_tree.find("OpenKfId").text
                next_cursor = ""  # 第一次请求时不需要提供 cursor

                latest_message = channel.get_latest_message(token, open_kfid, next_cursor)
                logger.debug(f"[wechatcs] latest_message: {latest_message}")
                try:
                    wechatcom_copy_msg = WechatComServiceMessage(msg=latest_message, client=channel.client)
                    logger.debug(f"[wechatcs] wechatcom_copy_msg: {wechatcom_copy_msg}")
                except NotImplementedError as e:
                    logger.debug("[wechatcs] " + str(e))
                    return "success"
                context = channel._compose_context(
                    wechatcom_copy_msg.ctype,
                    wechatcom_copy_msg.content,
                    isgroup=False,
                    msg=wechatcom_copy_msg,
                )
                logger.debug(f"[wechatcs] context: {context}")
                if context:
                    channel.produce(context)
                logger.debug(f"[wechatcs] get latest message: {latest_message}")
                return json.dumps({"status": "success"})
            else:
                return "Unsupported event type"
        except (InvalidSignatureException, InvalidCorpIdException) as e:
            logger.error(f"[wechatcs] Error: {e}")
            raise web.Forbidden()
        except ET.ParseError as e:
            logger.error(f"[wechatcs] XML Parse Error: {e}")
            return "Invalid XML format"
