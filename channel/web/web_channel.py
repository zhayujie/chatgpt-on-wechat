import sys
import time
import web
import json
import uuid
import io
from queue import Queue, Empty
from bridge.context import *
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel, check_prefix
from channel.chat_message import ChatMessage
from common.log import logger
from common.singleton import singleton
from config import conf
import os
import mimetypes  # 添加这行来处理MIME类型
import threading
import logging

class WebMessage(ChatMessage):
    def __init__(
        self,
        msg_id,
        content,
        ctype=ContextType.TEXT,
        from_user_id="User",
        to_user_id="Chatgpt",
        other_user_id="Chatgpt",
    ):
        self.msg_id = msg_id
        self.ctype = ctype
        self.content = content
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.other_user_id = other_user_id


@singleton
class WebChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = [ReplyType.VOICE]
    _instance = None
    
    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super(WebChannel, cls).__new__(cls)
    #     return cls._instance

    def __init__(self):
        super().__init__()
        self.msg_id_counter = 0  # 添加消息ID计数器
        self.session_queues = {}  # 存储session_id到队列的映射
        self.request_to_session = {}  # 存储request_id到session_id的映射


    def _generate_msg_id(self):
        """生成唯一的消息ID"""
        self.msg_id_counter += 1
        return str(int(time.time())) + str(self.msg_id_counter)

    def _generate_request_id(self):
        """生成唯一的请求ID"""
        return str(uuid.uuid4())

    def send(self, reply: Reply, context: Context):
        try:
            if reply.type in self.NOT_SUPPORT_REPLYTYPE:
                logger.warning(f"Web channel doesn't support {reply.type} yet")
                return

            if reply.type == ReplyType.IMAGE_URL:
                time.sleep(0.5)

            # 获取请求ID和会话ID
            request_id = context.get("request_id", None)
            
            if not request_id:
                logger.error("No request_id found in context, cannot send message")
                return
                
            # 通过request_id获取session_id
            session_id = self.request_to_session.get(request_id)
            if not session_id:
                logger.error(f"No session_id found for request {request_id}")
                return
            
            # 检查是否有会话队列
            if session_id in self.session_queues:
                # 创建响应数据，包含请求ID以区分不同请求的响应
                response_data = {
                    "type": str(reply.type),
                    "content": reply.content,
                    "timestamp": time.time(),
                    "request_id": request_id
                }
                self.session_queues[session_id].put(response_data)
                logger.debug(f"Response sent to queue for session {session_id}, request {request_id}")
            else:
                logger.warning(f"No response queue found for session {session_id}, response dropped")
            
        except Exception as e:
            logger.error(f"Error in send method: {e}")

    def post_message(self):
        """
        Handle incoming messages from users via POST request.
        Returns a request_id for tracking this specific request.
        """
        try:
            data = web.data()  # 获取原始POST数据
            json_data = json.loads(data)
            session_id = json_data.get('session_id', f'session_{int(time.time())}')
            prompt = json_data.get('message', '')
            
            # 生成请求ID
            request_id = self._generate_request_id()
            
            # 将请求ID与会话ID关联
            self.request_to_session[request_id] = session_id
            
            # 确保会话队列存在
            if session_id not in self.session_queues:
                self.session_queues[session_id] = Queue()
            
            # Web channel 不需要前缀，确保消息能通过前缀检查
            trigger_prefixs = conf().get("single_chat_prefix", [""])
            if check_prefix(prompt, trigger_prefixs) is None:
                # 如果没有匹配到前缀，给消息加上第一个前缀
                if trigger_prefixs:
                    prompt = trigger_prefixs[0] + prompt
                    logger.debug(f"[WebChannel] Added prefix to message: {prompt}")
            
            # 创建消息对象
            msg = WebMessage(self._generate_msg_id(), prompt)
            msg.from_user_id = session_id  # 使用会话ID作为用户ID
            
            # 创建上下文，明确指定 isgroup=False
            context = self._compose_context(ContextType.TEXT, prompt, msg=msg, isgroup=False)
            
            # 检查 context 是否为 None（可能被插件过滤等）
            if context is None:
                logger.warning(f"[WebChannel] Context is None for session {session_id}, message may be filtered")
                return json.dumps({"status": "error", "message": "Message was filtered"})

            # 覆盖必要的字段（_compose_context 会设置默认值，但我们需要使用实际的 session_id）
            context["session_id"] = session_id
            context["receiver"] = session_id
            context["request_id"] = request_id
            
            # 异步处理消息 - 只传递上下文
            threading.Thread(target=self.produce, args=(context,)).start()
            
            # 返回请求ID
            return json.dumps({"status": "success", "request_id": request_id})
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def poll_response(self):
        """
        Poll for responses using the session_id.
        """
        try:
            data = web.data()
            json_data = json.loads(data)
            session_id = json_data.get('session_id')
            
            if not session_id or session_id not in self.session_queues:
                return json.dumps({"status": "error", "message": "Invalid session ID"})
            
            # 尝试从队列获取响应，不等待
            try:
                # 使用peek而不是get，这样如果前端没有成功处理，下次还能获取到
                response = self.session_queues[session_id].get(block=False)
                
                # 返回响应，包含请求ID以区分不同请求
                return json.dumps({
                    "status": "success", 
                    "has_content": True,
                    "content": response["content"],
                    "request_id": response["request_id"],
                    "timestamp": response["timestamp"]
                })
                
            except Empty:
                # 没有新响应
                return json.dumps({"status": "success", "has_content": False})
                
        except Exception as e:
            logger.error(f"Error polling response: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def chat_page(self):
        """Serve the chat HTML page."""
        file_path = os.path.join(os.path.dirname(__file__), 'chat.html')  # 使用绝对路径
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def startup(self):
        port = conf().get("web_port", 9899)
        
        # 打印可用渠道类型提示
        logger.info("[WebChannel] 当前channel为web，可修改 config.json 配置文件中的 channel_type 字段进行切换。全部可用类型为：")
        logger.info("[WebChannel]   1. web              - 网页")
        logger.info("[WebChannel]   2. terminal         - 终端")
        logger.info("[WebChannel]   3. feishu           - 飞书")
        logger.info("[WebChannel]   4. dingtalk         - 钉钉")
        logger.info("[WebChannel]   5. wechatcom_app    - 企微自建应用")
        logger.info("[WebChannel]   6. wechatmp         - 个人公众号")
        logger.info("[WebChannel]   7. wechatmp_service - 企业公众号")
        logger.info(f"[WebChannel] 🌐 本地访问: http://localhost:{port}/chat")
        logger.info(f"[WebChannel] 🌍 服务器访问: http://YOUR_IP:{port}/chat (请将YOUR_IP替换为服务器IP)")
        logger.info("[WebChannel] ✅ Web对话网页已运行")
        
        # 确保静态文件目录存在
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            logger.debug(f"[WebChannel] Created static directory: {static_dir}")
        
        urls = (
            '/', 'RootHandler',
            '/message', 'MessageHandler',
            '/poll', 'PollHandler',
            '/chat', 'ChatHandler',
            '/config', 'ConfigHandler',
            '/assets/(.*)', 'AssetsHandler',
        )
        app = web.application(urls, globals(), autoreload=False)
        
        # 完全禁用web.py的HTTP日志输出
        web.httpserver.LogMiddleware.log = lambda self, status, environ: None
        
        # 配置web.py的日志级别为ERROR
        logging.getLogger("web").setLevel(logging.ERROR)
        logging.getLogger("web.httpserver").setLevel(logging.ERROR)
        
        # 抑制 web.py 默认的服务器启动消息
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))
        finally:
            sys.stdout = old_stdout


class RootHandler:
    def GET(self):
        # 重定向到/chat
        raise web.seeother('/chat')


class MessageHandler:
    def POST(self):
        return WebChannel().post_message()


class PollHandler:
    def POST(self):
        return WebChannel().poll_response()


class ChatHandler:
    def GET(self):
        # 正常返回聊天页面
        file_path = os.path.join(os.path.dirname(__file__), 'chat.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


class ConfigHandler:
    def GET(self):
        """返回前端需要的配置信息"""
        try:
            use_agent = conf().get("agent", False)
            
            if use_agent:
                title = "CowAgent"
                subtitle = "我可以帮你解答问题、管理计算机、创造和执行技能，并通过长期记忆不断成长"
            else:
                title = "AI 助手"
                subtitle = "我可以回答问题、提供信息或者帮助您完成各种任务"
            
            return json.dumps({
                "status": "success",
                "use_agent": use_agent,
                "title": title,
                "subtitle": subtitle
            })
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return json.dumps({"status": "error", "message": str(e)})


class AssetsHandler:
    def GET(self, file_path):  # 修改默认参数
        try:
            # 如果请求是/static/，需要处理
            if file_path == '':
                # 返回目录列表...
                pass

            # 获取当前文件的绝对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            static_dir = os.path.join(current_dir, 'static')

            full_path = os.path.normpath(os.path.join(static_dir, file_path))

            # 安全检查：确保请求的文件在static目录内
            if not os.path.abspath(full_path).startswith(os.path.abspath(static_dir)):
                logger.error(f"Security check failed for path: {full_path}")
                raise web.notfound()

            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                logger.error(f"File not found: {full_path}")
                raise web.notfound()

            # 设置正确的Content-Type
            content_type = mimetypes.guess_type(full_path)[0]
            if content_type:
                web.header('Content-Type', content_type)
            else:
                # 默认为二进制流
                web.header('Content-Type', 'application/octet-stream')

            # 读取并返回文件内容
            with open(full_path, 'rb') as f:
                return f.read()

        except Exception as e:
            logger.error(f"Error serving static file: {e}", exc_info=True)  # 添加更详细的错误信息
            raise web.notfound()
