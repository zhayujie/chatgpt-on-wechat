import sys
import time
import web
import json
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
        self.message_queues = {}  # 为每个用户存储一个消息队列
        self.msg_id_counter = 0  # 添加消息ID计数器

    def _generate_msg_id(self):
        """生成唯一的消息ID"""
        self.msg_id_counter += 1
        return str(int(time.time())) + str(self.msg_id_counter)

    def send(self, reply: Reply, context: Context):
        try:
            if reply.type in self.NOT_SUPPORT_REPLYTYPE:
                logger.warning(f"Web channel doesn't support {reply.type} yet")
                return
            
            # 获取用户ID
            user_id = context.get("receiver", None)
            if not user_id:
                logger.error("No receiver found in context, cannot send message")
                return
            
            # 检查是否有响应队列
            response_queue = context.get("response_queue", None)
            if response_queue:
                # 直接将响应放入队列
                response_data = {
                    "type": str(reply.type),
                    "content": reply.content,
                    "timestamp": time.time()
                }
                response_queue.put(response_data)
                logger.debug(f"Response sent to queue for user {user_id}")
            else:
                logger.warning(f"No response queue found for user {user_id}, response dropped")
            
        except Exception as e:
            logger.error(f"Error in send method: {e}")

    def post_message(self):
        """
        Handle incoming messages from users via POST request.
        """
        try:
            data = web.data()  # 获取原始POST数据
            json_data = json.loads(data)
            user_id = json_data.get('user_id', 'default_user')
            prompt = json_data.get('message', '')
            session_id = json_data.get('session_id', f'session_{int(time.time())}')
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
        
        if not prompt:
            return json.dumps({"status": "error", "message": "No message provided"})
            
        try:
            msg_id = self._generate_msg_id()
            web_message = WebMessage(
                msg_id=msg_id, 
                content=prompt,
                from_user_id=user_id,
                to_user_id="Chatgpt",
                other_user_id=user_id
            )
            
            context = self._compose_context(ContextType.TEXT, prompt, msg=web_message)
            if not context:
                return json.dumps({"status": "error", "message": "Failed to process message"})

            # 创建一个响应队列
            response_queue = Queue()
            
            # 确保上下文包含必要的信息
            context["isgroup"] = False
            context["receiver"] = user_id
            context["session_id"] = user_id
            context["response_queue"] = response_queue
                
            # 发送消息到处理队列
            self.produce(context)
            
            # 等待响应，最多等待30秒
            try:
                response = response_queue.get(timeout=30)
                return json.dumps({"status": "success", "reply": response["content"]})
            except Empty:
                return json.dumps({"status": "error", "message": "Response timeout"})
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return json.dumps({"status": "error", "message": "Internal server error"})

    def chat_page(self):
        """Serve the chat HTML page."""
        file_path = os.path.join(os.path.dirname(__file__), 'chat.html')  # 使用绝对路径
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def startup(self):
        print("\nWeb Channel is running, please visit http://localhost:9899/chat")
        
        # 确保静态文件目录存在
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            logger.info(f"Created static directory: {static_dir}")
        
        urls = (
            '/message', 'MessageHandler',
            '/chat', 'ChatHandler',
            '/assets/(.*)', 'AssetsHandler',  # 匹配 /assets/任何路径
        )
        port = conf().get("web_port", 9899)
        app = web.application(urls, globals(), autoreload=False)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))


class MessageHandler:
    def POST(self):
        return WebChannel().post_message()


class ChatHandler:
    def GET(self):
        # 正常返回聊天页面
        file_path = os.path.join(os.path.dirname(__file__), 'chat.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


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

            # 打印调试信息
            logger.info(f"Current directory: {current_dir}")
            logger.info(f"Static directory: {static_dir}")
            logger.info(f"Requested file: {file_path}")

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
