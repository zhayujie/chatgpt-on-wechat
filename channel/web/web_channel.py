import sys
import time
import web
import json
from queue import Queue
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
            
            if reply.type == ReplyType.IMAGE:
                from PIL import Image

                image_storage = reply.content
                image_storage.seek(0)
                img = Image.open(image_storage)
                print("<IMAGE>")
                img.show()
            elif reply.type == ReplyType.IMAGE_URL:
                import io

                import requests
                from PIL import Image

                img_url = reply.content
                pic_res = requests.get(img_url, stream=True)
                image_storage = io.BytesIO()
                for block in pic_res.iter_content(1024):
                    image_storage.write(block)
                image_storage.seek(0)
                img = Image.open(image_storage)
                print(img_url)
                img.show()
            else:
                print(reply.content)

            # 获取用户ID
            user_id = context.get("receiver", None)
            if not user_id:
                logger.error("No receiver found in context, cannot send message")
                return
            
            # 确保用户有对应的消息队列
            if user_id not in self.message_queues:
                self.message_queues[user_id] = Queue()
                logger.debug(f"Created message queue for user {user_id}")
                
            # 将消息放入对应用户的队列
            message_data = {
                "type": str(reply.type),
                "content": reply.content,
                "timestamp": time.time()  # 使用 Unix 时间戳
            }
            self.message_queues[user_id].put(message_data)
            logger.debug(f"Message queued for user {user_id}: {reply.content[:30]}...")
            
        except Exception as e:
            logger.error(f"Error in send method: {e}")

    def sse_handler(self, user_id):
        """
        Handle Server-Sent Events (SSE) for real-time communication.
        """
        web.header('Content-Type', 'text/event-stream')
        web.header('Cache-Control', 'no-cache')
        web.header('Connection', 'keep-alive')
        
        logger.debug(f"SSE connection established for user {user_id}")
        
        # 确保用户有消息队列
        if user_id not in self.message_queues:
            self.message_queues[user_id] = Queue()
            logger.debug(f"Created new message queue for user {user_id}")
        
        try:    
            while True:
                try:
                    # 发送心跳
                    yield f": heartbeat\n\n"
                    
                    # 非阻塞方式获取消息
                    if user_id in self.message_queues and not self.message_queues[user_id].empty():
                        message = self.message_queues[user_id].get_nowait()
                        logger.debug(f"Sending message to user {user_id}: {message}")
                        data = json.dumps(message)
                        yield f"data: {data}\n\n"
                        logger.debug(f"Message sent to user {user_id}")
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"SSE Error for user {user_id}: {str(e)}")
                    break
        finally:
            # 清理资源
            logger.debug(f"SSE connection closed for user {user_id}")

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
                to_user_id="Chatgpt",  # 明确指定接收者
                other_user_id=user_id
            )
            
            context = self._compose_context(ContextType.TEXT, prompt, msg=web_message)
            if not context:
                return json.dumps({"status": "error", "message": "Failed to process message"})

            # 确保上下文包含必要的信息
            context["isgroup"] = False
            context["receiver"] = user_id  # 添加接收者信息，用于send方法中识别用户
            context["session_id"] = session_id  # 添加会话ID
                
            self.produce(context)
            return json.dumps({"status": "success", "message": "Message received"})
            
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
            '/sse/(.+)', 'SSEHandler',
            '/poll/(.+)', 'PollHandler',
            '/message', 'MessageHandler',
            '/chat', 'ChatHandler',
            '/assets/(.*)', 'AssetsHandler',  # 匹配 /static/任何路径
        )
        port = conf().get("web_port", 9899)
        app = web.application(urls, globals(), autoreload=False)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def poll_messages(self, user_id):
        """Poll for new messages."""
        messages = []
        
        if user_id in self.message_queues:
            while not self.message_queues[user_id].empty():
                messages.append(self.message_queues[user_id].get_nowait())
        
        return json.dumps(messages)


class SSEHandler:
    def GET(self, user_id):
        return WebChannel().sse_handler(user_id)


class MessageHandler:
    def POST(self):
        return WebChannel().post_message()


class ChatHandler:
    def GET(self):
        # 正常返回聊天页面
        file_path = os.path.join(os.path.dirname(__file__), 'chat.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


# 添加轮询处理器
class PollHandler:
    def GET(self, user_id):
        web.header('Content-Type', 'application/json')
        return WebChannel().poll_messages(user_id)


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
