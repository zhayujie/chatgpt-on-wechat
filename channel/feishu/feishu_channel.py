"""
飞书通道接入

支持两种事件接收模式:
1. webhook模式: 通过HTTP服务器接收事件(需要公网IP)
2. websocket模式: 通过长连接接收事件(本地开发友好)

通过配置项 feishu_event_mode 选择模式: "webhook" 或 "websocket"

@author Saboteur7
@Date 2023/11/19
"""

import json
import os
import threading
# -*- coding=utf-8 -*-
import uuid

import requests
import web

from bridge.context import Context
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel, check_prefix
from channel.feishu.feishu_message import FeishuMessage
from common import utils
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from config import conf

URL_VERIFICATION = "url_verification"

# 尝试导入飞书SDK,如果未安装则websocket模式不可用
try:
    import lark_oapi as lark

    LARK_SDK_AVAILABLE = True
except ImportError:
    LARK_SDK_AVAILABLE = False
    logger.warning(
        "[FeiShu] lark_oapi not installed, websocket mode is not available. Install with: pip install lark-oapi")


@singleton
class FeiShuChanel(ChatChannel):
    feishu_app_id = conf().get('feishu_app_id')
    feishu_app_secret = conf().get('feishu_app_secret')
    feishu_token = conf().get('feishu_token')
    feishu_event_mode = conf().get('feishu_event_mode', 'websocket')  # webhook 或 websocket

    def __init__(self):
        super().__init__()
        # 历史消息id暂存，用于幂等控制
        self.receivedMsgs = ExpiredDict(60 * 60 * 7.1)
        logger.info("[FeiShu] app_id={}, app_secret={}, verification_token={}, event_mode={}".format(
            self.feishu_app_id, self.feishu_app_secret, self.feishu_token, self.feishu_event_mode))
        # 无需群校验和前缀
        conf()["group_name_white_list"] = ["ALL_GROUP"]
        conf()["single_chat_prefix"] = [""]

        # 验证配置
        if self.feishu_event_mode == 'websocket' and not LARK_SDK_AVAILABLE:
            logger.error("[FeiShu] websocket mode requires lark_oapi. Please install: pip install lark-oapi")
            raise Exception("lark_oapi not installed")

    def startup(self):
        if self.feishu_event_mode == 'websocket':
            self._startup_websocket()
        else:
            self._startup_webhook()

    def _startup_webhook(self):
        """启动HTTP服务器接收事件(webhook模式)"""
        logger.info("[FeiShu] Starting in webhook mode...")
        urls = (
            '/', 'channel.feishu.feishu_channel.FeishuController'
        )
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("feishu_port", 9891)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def _startup_websocket(self):
        """启动长连接接收事件(websocket模式)"""
        logger.info("[FeiShu] Starting in websocket mode...")

        # 创建事件处理器
        def handle_message_event(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
            """处理接收消息事件 v2.0"""
            try:
                logger.debug(f"[FeiShu] websocket receive event: {lark.JSON.marshal(data, indent=2)}")

                # 转换为标准的event格式
                event_dict = json.loads(lark.JSON.marshal(data))
                event = event_dict.get("event", {})

                # 处理消息
                self._handle_message_event(event)

            except Exception as e:
                logger.error(f"[FeiShu] websocket handle message error: {e}", exc_info=True)

        # 构建事件分发器
        event_handler = lark.EventDispatcherHandler.builder("", "") \
            .register_p2_im_message_receive_v1(handle_message_event) \
            .build()

        # 创建长连接客户端
        ws_client = lark.ws.Client(
            self.feishu_app_id,
            self.feishu_app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.DEBUG if conf().get("debug") else lark.LogLevel.INFO
        )

        # 在新线程中启动客户端，避免阻塞主线程
        def start_client():
            try:
                logger.info("[FeiShu] Websocket client starting...")
                ws_client.start()
            except Exception as e:
                logger.error(f"[FeiShu] Websocket client error: {e}", exc_info=True)

        ws_thread = threading.Thread(target=start_client, daemon=True)
        ws_thread.start()

        # 保持主线程运行
        logger.info("[FeiShu] Websocket mode started, waiting for events...")
        ws_thread.join()

    def _handle_message_event(self, event: dict):
        """
        处理消息事件的核心逻辑
        webhook和websocket模式共用此方法
        """
        if not event.get("message") or not event.get("sender"):
            logger.warning(f"[FeiShu] invalid message, event={event}")
            return

        msg = event.get("message")

        # 幂等判断
        msg_id = msg.get("message_id")
        if self.receivedMsgs.get(msg_id):
            logger.warning(f"[FeiShu] repeat msg filtered, msg_id={msg_id}")
            return
        self.receivedMsgs[msg_id] = True

        is_group = False
        chat_type = msg.get("chat_type")

        if chat_type == "group":
            if not msg.get("mentions") and msg.get("message_type") == "text":
                # 群聊中未@不响应
                return
            if msg.get("mentions") and msg.get("mentions")[0].get("name") != conf().get("feishu_bot_name") and msg.get(
                    "message_type") == "text":
                # 不是@机器人，不响应
                return
            # 群聊
            is_group = True
            receive_id_type = "chat_id"
        elif chat_type == "p2p":
            receive_id_type = "open_id"
        else:
            logger.warning("[FeiShu] message ignore")
            return

        # 构造飞书消息对象
        feishu_msg = FeishuMessage(event, is_group=is_group, access_token=self.fetch_access_token())
        if not feishu_msg:
            return

        context = self._compose_context(
            feishu_msg.ctype,
            feishu_msg.content,
            isgroup=is_group,
            msg=feishu_msg,
            receive_id_type=receive_id_type,
            no_need_at=True
        )
        if context:
            self.produce(context)
        logger.info(f"[FeiShu] query={feishu_msg.content}, type={feishu_msg.ctype}")

    def send(self, reply: Reply, context: Context):
        msg = context.get("msg")
        is_group = context["isgroup"]
        if msg:
            access_token = msg.access_token
        else:
            access_token = self.fetch_access_token()
        headers = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
        }
        msg_type = "text"
        logger.info(f"[FeiShu] start send reply message, type={context.type}, content={reply.content}")
        reply_content = reply.content
        content_key = "text"
        if reply.type == ReplyType.IMAGE_URL:
            # 图片上传
            reply_content = self._upload_image_url(reply.content, access_token)
            if not reply_content:
                logger.warning("[FeiShu] upload image failed")
                return
            msg_type = "image"
            content_key = "image_key"
        elif reply.type == ReplyType.FILE:
            # 判断是否为视频文件
            file_path = reply.content
            if file_path.startswith("file://"):
                file_path = file_path[7:]
            
            is_video = file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv'))
            
            if is_video:
                # 视频使用 media 类型
                file_key = self._upload_video_url(reply.content, access_token)
                if not file_key:
                    logger.warning("[FeiShu] upload video failed")
                    return
                reply_content = file_key
                msg_type = "media"
                content_key = "file_key"
            else:
                # 其他文件使用 file 类型
                file_key = self._upload_file_url(reply.content, access_token)
                if not file_key:
                    logger.warning("[FeiShu] upload file failed")
                    return
                reply_content = file_key
                msg_type = "file"
                content_key = "file_key"
        
        # Check if we can reply to an existing message (need msg_id)
        can_reply = is_group and msg and hasattr(msg, 'msg_id') and msg.msg_id
        
        if can_reply:
            # 群聊中回复已有消息
            url = f"https://open.feishu.cn/open-apis/im/v1/messages/{msg.msg_id}/reply"
            data = {
                "msg_type": msg_type,
                "content": json.dumps({content_key: reply_content})
            }
            res = requests.post(url=url, headers=headers, json=data, timeout=(5, 10))
        else:
            # 发送新消息（私聊或群聊中无msg_id的情况，如定时任务）
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            params = {"receive_id_type": context.get("receive_id_type") or "open_id"}
            data = {
                "receive_id": context.get("receiver"),
                "msg_type": msg_type,
                "content": json.dumps({content_key: reply_content})
            }
            res = requests.post(url=url, headers=headers, params=params, json=data, timeout=(5, 10))
        res = res.json()
        if res.get("code") == 0:
            logger.info(f"[FeiShu] send message success")
        else:
            logger.error(f"[FeiShu] send message failed, code={res.get('code')}, msg={res.get('msg')}")


    def fetch_access_token(self) -> str:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {
            "Content-Type": "application/json"
        }
        req_body = {
            "app_id": self.feishu_app_id,
            "app_secret": self.feishu_app_secret
        }
        data = bytes(json.dumps(req_body), encoding='utf8')
        response = requests.post(url=url, data=data, headers=headers)
        if response.status_code == 200:
            res = response.json()
            if res.get("code") != 0:
                logger.error(f"[FeiShu] get tenant_access_token error, code={res.get('code')}, msg={res.get('msg')}")
                return ""
            else:
                return res.get("tenant_access_token")
        else:
            logger.error(f"[FeiShu] fetch token error, res={response}")


    def _upload_image_url(self, img_url, access_token):
        logger.debug(f"[FeiShu] start process image, img_url={img_url}")
        
        # Check if it's a local file path (file:// protocol)
        if img_url.startswith("file://"):
            local_path = img_url[7:]  # Remove "file://" prefix
            logger.info(f"[FeiShu] uploading local file: {local_path}")
            
            if not os.path.exists(local_path):
                logger.error(f"[FeiShu] local file not found: {local_path}")
                return None
            
            # Upload directly from local file
            upload_url = "https://open.feishu.cn/open-apis/im/v1/images"
            data = {'image_type': 'message'}
            headers = {'Authorization': f'Bearer {access_token}'}
            
            with open(local_path, "rb") as file:
                upload_response = requests.post(upload_url, files={"image": file}, data=data, headers=headers)
                logger.info(f"[FeiShu] upload file, res={upload_response.content}")
                
                response_data = upload_response.json()
                if response_data.get("code") == 0:
                    return response_data.get("data").get("image_key")
                else:
                    logger.error(f"[FeiShu] upload failed: {response_data}")
                    return None
        
        # Original logic for HTTP URLs
        response = requests.get(img_url)
        suffix = utils.get_path_suffix(img_url)
        temp_name = str(uuid.uuid4()) + "." + suffix
        if response.status_code == 200:
            # 将图片内容保存为临时文件
            with open(temp_name, "wb") as file:
                file.write(response.content)

        # upload
        upload_url = "https://open.feishu.cn/open-apis/im/v1/images"
        data = {
            'image_type': 'message'
        }
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        with open(temp_name, "rb") as file:
            upload_response = requests.post(upload_url, files={"image": file}, data=data, headers=headers)
            logger.info(f"[FeiShu] upload file, res={upload_response.content}")
            os.remove(temp_name)
            return upload_response.json().get("data").get("image_key")

    def _upload_video_url(self, video_url, access_token):
        """
        Upload video to Feishu and return file_key (for media type messages)
        Supports:
        - file:// URLs for local files
        - http(s):// URLs (download then upload)
        """
        # For file:// URLs (local files), upload directly
        if video_url.startswith("file://"):
            local_path = video_url[7:]  # Remove file:// prefix
            if not os.path.exists(local_path):
                logger.error(f"[FeiShu] local video file not found: {local_path}")
                return None
            
            file_name = os.path.basename(local_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Determine file type for Feishu API (for media messages)
            # Media type only supports mp4
            file_type_map = {
                '.mp4': 'mp4',
            }
            file_type = file_type_map.get(file_ext, 'mp4')  # Default to mp4
            
            # Upload video to Feishu (use file upload API, but send as media type)
            upload_url = "https://open.feishu.cn/open-apis/im/v1/files"
            data = {'file_type': file_type, 'file_name': file_name}
            headers = {'Authorization': f'Bearer {access_token}'}
            
            try:
                with open(local_path, "rb") as file:
                    upload_response = requests.post(
                        upload_url, 
                        files={"file": file}, 
                        data=data, 
                        headers=headers,
                        timeout=(5, 60)  # 5s connect, 60s read timeout (videos are larger)
                    )
                    logger.info(f"[FeiShu] upload video response, status={upload_response.status_code}, res={upload_response.content}")
                    
                    response_data = upload_response.json()
                    if response_data.get("code") == 0:
                        return response_data.get("data").get("file_key")
                    else:
                        logger.error(f"[FeiShu] upload video failed: {response_data}")
                        return None
            except Exception as e:
                logger.error(f"[FeiShu] upload video exception: {e}")
                return None
        
        # For HTTP URLs, download first then upload
        try:
            logger.info(f"[FeiShu] Downloading video from URL: {video_url}")
            response = requests.get(video_url, timeout=(5, 60))
            if response.status_code != 200:
                logger.error(f"[FeiShu] download video failed, status={response.status_code}")
                return None
            
            # Save to temp file
            import uuid
            file_name = os.path.basename(video_url) or "video.mp4"
            temp_name = str(uuid.uuid4()) + "_" + file_name
            
            with open(temp_name, "wb") as file:
                file.write(response.content)
            
            logger.info(f"[FeiShu] Video downloaded, size={len(response.content)} bytes, uploading...")
            
            # Upload
            file_ext = os.path.splitext(file_name)[1].lower()
            file_type_map = {
                '.mp4': 'mp4',
            }
            file_type = file_type_map.get(file_ext, 'mp4')
            
            upload_url = "https://open.feishu.cn/open-apis/im/v1/files"
            data = {'file_type': file_type, 'file_name': file_name}
            headers = {'Authorization': f'Bearer {access_token}'}
            
            with open(temp_name, "rb") as file:
                upload_response = requests.post(upload_url, files={"file": file}, data=data, headers=headers, timeout=(5, 60))
                logger.info(f"[FeiShu] upload video, res={upload_response.content}")
                
                response_data = upload_response.json()
                os.remove(temp_name)  # Clean up temp file
                
                if response_data.get("code") == 0:
                    return response_data.get("data").get("file_key")
                else:
                    logger.error(f"[FeiShu] upload video failed: {response_data}")
                    return None
        except Exception as e:
            logger.error(f"[FeiShu] upload video from URL exception: {e}")
            # Clean up temp file if exists
            if 'temp_name' in locals() and os.path.exists(temp_name):
                os.remove(temp_name)
            return None

    def _upload_file_url(self, file_url, access_token):
        """
        Upload file to Feishu
        Supports both local files (file://) and HTTP URLs
        """
        logger.debug(f"[FeiShu] start process file, file_url={file_url}")
        
        # Check if it's a local file path (file:// protocol)
        if file_url.startswith("file://"):
            local_path = file_url[7:]  # Remove "file://" prefix
            logger.info(f"[FeiShu] uploading local file: {local_path}")
            
            if not os.path.exists(local_path):
                logger.error(f"[FeiShu] local file not found: {local_path}")
                return None
            
            # Get file info
            file_name = os.path.basename(local_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Determine file type for Feishu API
            # Feishu supports: opus, mp4, pdf, doc, xls, ppt, stream (other types)
            file_type_map = {
                '.opus': 'opus',
                '.mp4': 'mp4',
                '.pdf': 'pdf',
                '.doc': 'doc', '.docx': 'doc',
                '.xls': 'xls', '.xlsx': 'xls',
                '.ppt': 'ppt', '.pptx': 'ppt',
            }
            file_type = file_type_map.get(file_ext, 'stream')  # Default to stream for other types
            
            # Upload file to Feishu
            upload_url = "https://open.feishu.cn/open-apis/im/v1/files"
            data = {'file_type': file_type, 'file_name': file_name}
            headers = {'Authorization': f'Bearer {access_token}'}
            
            try:
                with open(local_path, "rb") as file:
                    upload_response = requests.post(
                        upload_url, 
                        files={"file": file}, 
                        data=data, 
                        headers=headers,
                        timeout=(5, 30)  # 5s connect, 30s read timeout
                    )
                    logger.info(f"[FeiShu] upload file response, status={upload_response.status_code}, res={upload_response.content}")
                    
                    response_data = upload_response.json()
                    if response_data.get("code") == 0:
                        return response_data.get("data").get("file_key")
                    else:
                        logger.error(f"[FeiShu] upload file failed: {response_data}")
                        return None
            except Exception as e:
                logger.error(f"[FeiShu] upload file exception: {e}")
                return None
        
        # For HTTP URLs, download first then upload
        try:
            response = requests.get(file_url, timeout=(5, 30))
            if response.status_code != 200:
                logger.error(f"[FeiShu] download file failed, status={response.status_code}")
                return None
            
            # Save to temp file
            import uuid
            file_name = os.path.basename(file_url)
            temp_name = str(uuid.uuid4()) + "_" + file_name
            
            with open(temp_name, "wb") as file:
                file.write(response.content)
            
            # Upload
            file_ext = os.path.splitext(file_name)[1].lower()
            file_type_map = {
                '.opus': 'opus', '.mp4': 'mp4', '.pdf': 'pdf',
                '.doc': 'doc', '.docx': 'doc',
                '.xls': 'xls', '.xlsx': 'xls',
                '.ppt': 'ppt', '.pptx': 'ppt',
            }
            file_type = file_type_map.get(file_ext, 'stream')
            
            upload_url = "https://open.feishu.cn/open-apis/im/v1/files"
            data = {'file_type': file_type, 'file_name': file_name}
            headers = {'Authorization': f'Bearer {access_token}'}
            
            with open(temp_name, "rb") as file:
                upload_response = requests.post(upload_url, files={"file": file}, data=data, headers=headers)
                logger.info(f"[FeiShu] upload file, res={upload_response.content}")
                
                response_data = upload_response.json()
                os.remove(temp_name)  # Clean up temp file
                
                if response_data.get("code") == 0:
                    return response_data.get("data").get("file_key")
                else:
                    logger.error(f"[FeiShu] upload file failed: {response_data}")
                    return None
        except Exception as e:
            logger.error(f"[FeiShu] upload file from URL exception: {e}")
            return None

    def _compose_context(self, ctype: ContextType, content, **kwargs):
        context = Context(ctype, content)
        context.kwargs = kwargs
        if "origin_ctype" not in context:
            context["origin_ctype"] = ctype

        cmsg = context["msg"]
        
        # Set session_id based on chat type
        if cmsg.is_group:
            # Group chat: check if group_shared_session is enabled
            if conf().get("group_shared_session", True):
                # All users in the group share the same session context
                context["session_id"] = cmsg.other_user_id  # group_id
            else:
                # Each user has their own session within the group
                # This ensures:
                # - Same user in different groups have separate conversation histories
                # - Same user in private chat and group chat have separate histories
                context["session_id"] = f"{cmsg.from_user_id}:{cmsg.other_user_id}"
        else:
            # Private chat: use user_id only
            context["session_id"] = cmsg.from_user_id
        
        context["receiver"] = cmsg.other_user_id

        if ctype == ContextType.TEXT:
            # 1.文本请求
            # 图片生成处理
            img_match_prefix = check_prefix(content, conf().get("image_create_prefix"))
            if img_match_prefix:
                content = content.replace(img_match_prefix, "", 1)
                context.type = ContextType.IMAGE_CREATE
            else:
                context.type = ContextType.TEXT
            context.content = content.strip()

        elif context.type == ContextType.VOICE:
            # 2.语音请求
            if "desire_rtype" not in context and conf().get("voice_reply_voice"):
                context["desire_rtype"] = ReplyType.VOICE

        return context


class FeishuController:
    """
    HTTP服务器控制器，用于webhook模式
    """
    # 类常量
    FAILED_MSG = '{"success": false}'
    SUCCESS_MSG = '{"success": true}'
    MESSAGE_RECEIVE_TYPE = "im.message.receive_v1"

    def GET(self):
        return "Feishu service start success!"

    def POST(self):
        try:
            channel = FeiShuChanel()

            request = json.loads(web.data().decode("utf-8"))
            logger.debug(f"[FeiShu] receive request: {request}")

            # 1.事件订阅回调验证
            if request.get("type") == URL_VERIFICATION:
                varify_res = {"challenge": request.get("challenge")}
                return json.dumps(varify_res)

            # 2.消息接收处理
            # token 校验
            header = request.get("header")
            if not header or header.get("token") != channel.feishu_token:
                return self.FAILED_MSG

            # 处理消息事件
            event = request.get("event")
            if header.get("event_type") == self.MESSAGE_RECEIVE_TYPE and event:
                channel._handle_message_event(event)

            return self.SUCCESS_MSG

        except Exception as e:
            logger.error(e)
            return self.FAILED_MSG
