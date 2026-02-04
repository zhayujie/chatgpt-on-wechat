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
import ssl
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
        logger.debug("[FeiShu] app_id={}, app_secret={}, verification_token={}, event_mode={}".format(
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
        logger.debug("[FeiShu] Starting in webhook mode...")
        urls = (
            '/', 'channel.feishu.feishu_channel.FeishuController'
        )
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("feishu_port", 9891)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def _startup_websocket(self):
        """启动长连接接收事件(websocket模式)"""
        logger.debug("[FeiShu] Starting in websocket mode...")

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

        # 尝试连接，如果遇到SSL错误则自动禁用证书验证
        def start_client_with_retry():
            """启动websocket客户端，自动处理SSL证书错误"""
            # 全局禁用SSL证书验证（在导入lark_oapi之前设置）
            import ssl as ssl_module

            # 保存原始的SSL上下文创建方法
            original_create_default_context = ssl_module.create_default_context

            def create_unverified_context(*args, **kwargs):
                """创建一个不验证证书的SSL上下文"""
                context = original_create_default_context(*args, **kwargs)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                return context

            # 尝试正常连接，如果失败则禁用SSL验证
            for attempt in range(2):
                try:
                    if attempt == 1:
                        # 第二次尝试：禁用SSL验证
                        logger.warning("[FeiShu] SSL certificate verification disabled due to certificate error. "
                                       "This may happen when using corporate proxy or self-signed certificates.")
                        ssl_module.create_default_context = create_unverified_context
                        ssl_module._create_unverified_context = create_unverified_context

                    ws_client = lark.ws.Client(
                        self.feishu_app_id,
                        self.feishu_app_secret,
                        event_handler=event_handler,
                        log_level=lark.LogLevel.DEBUG if conf().get("debug") else lark.LogLevel.INFO
                    )

                    logger.debug("[FeiShu] Websocket client starting...")
                    ws_client.start()
                    # 如果成功启动，跳出循环
                    break

                except Exception as e:
                    error_msg = str(e)
                    # 检查是否是SSL证书验证错误
                    is_ssl_error = "CERTIFICATE_VERIFY_FAILED" in error_msg or "certificate verify failed" in error_msg.lower()

                    if is_ssl_error and attempt == 0:
                        # 第一次遇到SSL错误，记录日志并继续循环（下次会禁用验证）
                        logger.warning(f"[FeiShu] SSL certificate verification failed: {error_msg}")
                        logger.info("[FeiShu] Retrying connection with SSL verification disabled...")
                        continue
                    else:
                        # 其他错误或禁用验证后仍失败，抛出异常
                        logger.error(f"[FeiShu] Websocket client error: {e}", exc_info=True)
                        # 恢复原始方法
                        ssl_module.create_default_context = original_create_default_context
                        raise

            # 注意：不恢复原始方法，因为ws_client.start()会持续运行

        # 在新线程中启动客户端，避免阻塞主线程
        ws_thread = threading.Thread(target=start_client_with_retry, daemon=True)
        ws_thread.start()

        # 保持主线程运行
        logger.info("[FeiShu] ✅ Websocket connected, ready to receive messages")
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

        # 处理文件缓存逻辑
        from channel.file_cache import get_file_cache
        file_cache = get_file_cache()

        # 获取 session_id（用于缓存关联）
        if is_group:
            if conf().get("group_shared_session", True):
                session_id = msg.get("chat_id")  # 群共享会话
            else:
                session_id = feishu_msg.from_user_id + "_" + msg.get("chat_id")
        else:
            session_id = feishu_msg.from_user_id

        # 如果是单张图片消息，缓存起来
        if feishu_msg.ctype == ContextType.IMAGE:
            if hasattr(feishu_msg, 'image_path') and feishu_msg.image_path:
                file_cache.add(session_id, feishu_msg.image_path, file_type='image')
                logger.info(f"[FeiShu] Image cached for session {session_id}, waiting for user query...")
            # 单张图片不直接处理，等待用户提问
            return

        # 如果是文本消息，检查是否有缓存的文件
        if feishu_msg.ctype == ContextType.TEXT:
            cached_files = file_cache.get(session_id)
            if cached_files:
                # 将缓存的文件附加到文本消息中
                file_refs = []
                for file_info in cached_files:
                    file_path = file_info['path']
                    file_type = file_info['type']
                    if file_type == 'image':
                        file_refs.append(f"[图片: {file_path}]")
                    elif file_type == 'video':
                        file_refs.append(f"[视频: {file_path}]")
                    else:
                        file_refs.append(f"[文件: {file_path}]")

                feishu_msg.content = feishu_msg.content + "\n" + "\n".join(file_refs)
                logger.info(f"[FeiShu] Attached {len(cached_files)} cached file(s) to user query")
                # 清除缓存
                file_cache.clear(session_id)

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
        logger.debug(f"[FeiShu] query={feishu_msg.content}, type={feishu_msg.ctype}")

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
        logger.debug(f"[FeiShu] sending reply, type={context.type}, content={reply.content[:100]}...")
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
            # 如果有附加的文本内容，先发送文本
            if hasattr(reply, 'text_content') and reply.text_content:
                logger.info(f"[FeiShu] Sending text before file: {reply.text_content[:50]}...")
                text_reply = Reply(ReplyType.TEXT, reply.text_content)
                self._send(text_reply, context)
                import time
                time.sleep(0.3)  # 短暂延迟，确保文本先到达

            # 判断是否为视频文件
            file_path = reply.content
            if file_path.startswith("file://"):
                file_path = file_path[7:]

            is_video = file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv'))

            if is_video:
                # 视频上传（包含duration信息）
                upload_data = self._upload_video_url(reply.content, access_token)
                if not upload_data or not upload_data.get('file_key'):
                    logger.warning("[FeiShu] upload video failed")
                    return

                # 视频使用 media 类型（根据官方文档）
                # 错误码 230055 说明：上传 mp4 时必须使用 msg_type="media"
                msg_type = "media"
                reply_content = upload_data  # 完整的上传响应数据（包含file_key和duration）
                logger.info(
                    f"[FeiShu] Sending video: file_key={upload_data.get('file_key')}, duration={upload_data.get('duration')}ms")
                content_key = None  # 直接序列化整个对象
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

        # Build content JSON
        content_json = json.dumps(reply_content) if content_key is None else json.dumps({content_key: reply_content})
        logger.debug(f"[FeiShu] Sending message: msg_type={msg_type}, content={content_json[:200]}")

        if can_reply:
            # 群聊中回复已有消息
            url = f"https://open.feishu.cn/open-apis/im/v1/messages/{msg.msg_id}/reply"
            data = {
                "msg_type": msg_type,
                "content": content_json
            }
            res = requests.post(url=url, headers=headers, json=data, timeout=(5, 10))
        else:
            # 发送新消息（私聊或群聊中无msg_id的情况，如定时任务）
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            params = {"receive_id_type": context.get("receive_id_type") or "open_id"}
            data = {
                "receive_id": context.get("receiver"),
                "msg_type": msg_type,
                "content": content_json
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

    def _get_video_duration(self, file_path: str) -> int:
        """
        获取视频时长（毫秒）
        
        Args:
            file_path: 视频文件路径
        
        Returns:
            视频时长（毫秒），如果获取失败返回0
        """
        try:
            import subprocess

            # 使用 ffprobe 获取视频时长
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                duration_seconds = float(result.stdout.strip())
                duration_ms = int(duration_seconds * 1000)
                logger.info(f"[FeiShu] Video duration: {duration_seconds:.2f}s ({duration_ms}ms)")
                return duration_ms
            else:
                logger.warning(f"[FeiShu] Failed to get video duration via ffprobe: {result.stderr}")
                return 0
        except FileNotFoundError:
            logger.warning("[FeiShu] ffprobe not found, video duration will be 0. Install ffmpeg to fix this.")
            return 0
        except Exception as e:
            logger.warning(f"[FeiShu] Failed to get video duration: {e}")
            return 0

    def _upload_video_url(self, video_url, access_token):
        """
        Upload video to Feishu and return video info (file_key and duration)
        Supports:
        - file:// URLs for local files
        - http(s):// URLs (download then upload)
        
        Returns:
            dict with 'file_key' and 'duration' (milliseconds), or None if failed
        """
        local_path = None
        temp_file = None

        try:
            # For file:// URLs (local files), upload directly
            if video_url.startswith("file://"):
                local_path = video_url[7:]  # Remove file:// prefix
                if not os.path.exists(local_path):
                    logger.error(f"[FeiShu] local video file not found: {local_path}")
                    return None
            else:
                # For HTTP URLs, download first
                logger.info(f"[FeiShu] Downloading video from URL: {video_url}")
                response = requests.get(video_url, timeout=(5, 60))
                if response.status_code != 200:
                    logger.error(f"[FeiShu] download video failed, status={response.status_code}")
                    return None

                # Save to temp file
                import uuid
                file_name = os.path.basename(video_url) or "video.mp4"
                temp_file = str(uuid.uuid4()) + "_" + file_name

                with open(temp_file, "wb") as file:
                    file.write(response.content)

                logger.info(f"[FeiShu] Video downloaded, size={len(response.content)} bytes")
                local_path = temp_file

            # Get video duration
            duration = self._get_video_duration(local_path)

            # Upload to Feishu
            file_name = os.path.basename(local_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            file_type_map = {'.mp4': 'mp4'}
            file_type = file_type_map.get(file_ext, 'mp4')

            upload_url = "https://open.feishu.cn/open-apis/im/v1/files"
            data = {
                'file_type': file_type,
                'file_name': file_name
            }
            # Add duration only if available (required for video/audio)
            if duration:
                data['duration'] = duration  # Must be int, not string

            headers = {'Authorization': f'Bearer {access_token}'}

            logger.info(f"[FeiShu] Uploading video: file_name={file_name}, duration={duration}ms")

            with open(local_path, "rb") as file:
                upload_response = requests.post(
                    upload_url,
                    files={"file": file},
                    data=data,
                    headers=headers,
                    timeout=(5, 60)
                )
                logger.info(
                    f"[FeiShu] upload video response, status={upload_response.status_code}, res={upload_response.content}")

                response_data = upload_response.json()
                if response_data.get("code") == 0:
                    # Add duration to the response data (API doesn't return it)
                    upload_data = response_data.get("data")
                    upload_data['duration'] = duration  # Add our calculated duration
                    logger.info(
                        f"[FeiShu] Upload complete: file_key={upload_data.get('file_key')}, duration={duration}ms")
                    return upload_data
                else:
                    logger.error(f"[FeiShu] upload video failed: {response_data}")
                    return None

        except Exception as e:
            logger.error(f"[FeiShu] upload video exception: {e}")
            return None

        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"[FeiShu] Failed to remove temp file {temp_file}: {e}")

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
                    logger.info(
                        f"[FeiShu] upload file response, status={upload_response.status_code}, res={upload_response.content}")

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
