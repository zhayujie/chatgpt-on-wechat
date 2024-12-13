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

            # 获取用户ID，如果没有则使用默认值
            # user_id = getattr(context.get("session", None), "session_id", "default_user")
            user_id = context["receiver"]
            # 确保用户有对应的消息队列
            if user_id not in self.message_queues:
                self.message_queues[user_id] = Queue()
                
            # 将消息放入对应用户的队列
            message_data = {
                "type": str(reply.type),
                "content": reply.content,
                "timestamp": time.time()
            }
            self.message_queues[user_id].put(message_data)
            logger.debug(f"Message queued for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in send method: {e}")
            raise

    def sse_handler(self, user_id):
        """
        Handle Server-Sent Events (SSE) for real-time communication.
        """
        web.header('Content-Type', 'text/event-stream')
        web.header('Cache-Control', 'no-cache')
        web.header('Connection', 'keep-alive')
        
        # 确保用户有消息队列
        if user_id not in self.message_queues:
            self.message_queues[user_id] = Queue()
        
        try:    
            while True:
                try:
                    # 发送心跳
                    yield f": heartbeat\n\n"
                    
                    # 非阻塞方式获取消息
                    if not self.message_queues[user_id].empty():
                        message = self.message_queues[user_id].get_nowait()
                        yield f"data: {json.dumps(message)}\n\n"
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"SSE Error: {e}")
                    break
        finally:
            # 清理资源
            if user_id in self.message_queues:
                # 只有当队列为空时才删除
                if self.message_queues[user_id].empty():
                    del self.message_queues[user_id]

    def post_message(self):
        """
        Handle incoming messages from users via POST request.
        """
        try:
            data = web.data()  # 获取原始POST数据
            json_data = json.loads(data)
            user_id = json_data.get('user_id', 'default_user')
            prompt = json_data.get('message', '')
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
        
        if not prompt:
            return json.dumps({"status": "error", "message": "No message provided"})
            
        try:
            msg_id = self._generate_msg_id()
            context = self._compose_context(ContextType.TEXT, prompt, msg=WebMessage(msg_id, 
                                                                                     prompt,
                                                                                     from_user_id=user_id,
                                                                                     other_user_id = user_id
                                                                                     ))
            context["isgroup"] = False
            # context["session"] = web.storage(session_id=user_id)
            
            if not context:
                return json.dumps({"status": "error", "message": "Failed to process message"})
                
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
        logger.setLevel("WARN")
        print("\nWeb Channel is running. Send POST requests to /message to send messages.")
        
        urls = (
            '/sse/(.+)', 'SSEHandler',  # 修改路由以接收用户ID
            '/message', 'MessageHandler',
            '/chat', 'ChatHandler', 
        )
        port = conf().get("web_port", 9899)
        app = web.application(urls, globals(), autoreload=False)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))


class SSEHandler:
    def GET(self, user_id):
        return WebChannel().sse_handler(user_id)


class MessageHandler:
    def POST(self):
        return WebChannel().post_message()


class ChatHandler:
    def GET(self):
        return WebChannel().chat_page()
