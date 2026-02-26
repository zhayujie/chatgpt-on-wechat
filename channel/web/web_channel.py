import sys
import time
import web
import json
import uuid
from queue import Queue, Empty
from bridge.context import *
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel, check_prefix
from channel.chat_message import ChatMessage
from common.log import logger
from common.singleton import singleton
from config import conf
import os
import mimetypes
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
        self.msg_id_counter = 0
        self.session_queues = {}       # session_id -> Queue (fallback polling)
        self.request_to_session = {}   # request_id -> session_id
        self.sse_queues = {}           # request_id -> Queue (SSE streaming)
        self._http_server = None


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

            request_id = context.get("request_id", None)
            if not request_id:
                logger.error("No request_id found in context, cannot send message")
                return

            session_id = self.request_to_session.get(request_id)
            if not session_id:
                logger.error(f"No session_id found for request {request_id}")
                return

            # SSE mode: push done event to SSE queue
            if request_id in self.sse_queues:
                content = reply.content if reply.content is not None else ""
                self.sse_queues[request_id].put({
                    "type": "done",
                    "content": content,
                    "request_id": request_id,
                    "timestamp": time.time()
                })
                logger.debug(f"SSE done sent for request {request_id}")
                return

            # Fallback: polling mode
            if session_id in self.session_queues:
                response_data = {
                    "type": str(reply.type),
                    "content": reply.content,
                    "timestamp": time.time(),
                    "request_id": request_id
                }
                self.session_queues[session_id].put(response_data)
                logger.debug(f"Response sent to poll queue for session {session_id}, request {request_id}")
            else:
                logger.warning(f"No response queue found for session {session_id}, response dropped")

        except Exception as e:
            logger.error(f"Error in send method: {e}")

    def _make_sse_callback(self, request_id: str):
        """Build an on_event callback that pushes agent stream events into the SSE queue."""
        def on_event(event: dict):
            if request_id not in self.sse_queues:
                return
            q = self.sse_queues[request_id]
            event_type = event.get("type")
            data = event.get("data", {})

            if event_type == "message_update":
                delta = data.get("delta", "")
                if delta:
                    q.put({"type": "delta", "content": delta})

            elif event_type == "tool_execution_start":
                tool_name = data.get("tool_name", "tool")
                arguments = data.get("arguments", {})
                q.put({"type": "tool_start", "tool": tool_name, "arguments": arguments})

            elif event_type == "tool_execution_end":
                tool_name = data.get("tool_name", "tool")
                status = data.get("status", "success")
                result = data.get("result", "")
                exec_time = data.get("execution_time", 0)
                # Truncate long results to avoid huge SSE payloads
                result_str = str(result)
                if len(result_str) > 2000:
                    result_str = result_str[:2000] + "…"
                q.put({
                    "type": "tool_end",
                    "tool": tool_name,
                    "status": status,
                    "result": result_str,
                    "execution_time": round(exec_time, 2)
                })

        return on_event

    def post_message(self):
        """
        Handle incoming messages from users via POST request.
        Returns a request_id for tracking this specific request.
        """
        try:
            data = web.data()
            json_data = json.loads(data)
            session_id = json_data.get('session_id', f'session_{int(time.time())}')
            prompt = json_data.get('message', '')
            use_sse = json_data.get('stream', True)

            request_id = self._generate_request_id()
            self.request_to_session[request_id] = session_id

            if session_id not in self.session_queues:
                self.session_queues[session_id] = Queue()

            if use_sse:
                self.sse_queues[request_id] = Queue()

            trigger_prefixs = conf().get("single_chat_prefix", [""])
            if check_prefix(prompt, trigger_prefixs) is None:
                if trigger_prefixs:
                    prompt = trigger_prefixs[0] + prompt
                    logger.debug(f"[WebChannel] Added prefix to message: {prompt}")

            msg = WebMessage(self._generate_msg_id(), prompt)
            msg.from_user_id = session_id

            context = self._compose_context(ContextType.TEXT, prompt, msg=msg, isgroup=False)

            if context is None:
                logger.warning(f"[WebChannel] Context is None for session {session_id}, message may be filtered")
                if request_id in self.sse_queues:
                    del self.sse_queues[request_id]
                return json.dumps({"status": "error", "message": "Message was filtered"})

            context["session_id"] = session_id
            context["receiver"] = session_id
            context["request_id"] = request_id

            if use_sse:
                context["on_event"] = self._make_sse_callback(request_id)

            threading.Thread(target=self.produce, args=(context,)).start()

            return json.dumps({"status": "success", "request_id": request_id, "stream": use_sse})

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def stream_response(self, request_id: str):
        """
        SSE generator for a given request_id.
        Yields UTF-8 encoded bytes to avoid WSGI Latin-1 mangling.
        """
        if request_id not in self.sse_queues:
            yield b"data: {\"type\": \"error\", \"message\": \"invalid request_id\"}\n\n"
            return

        q = self.sse_queues[request_id]
        timeout = 300  # 5 minutes max
        deadline = time.time() + timeout

        try:
            while time.time() < deadline:
                try:
                    item = q.get(timeout=1)
                except Empty:
                    yield b": keepalive\n\n"
                    continue

                payload = json.dumps(item, ensure_ascii=False)
                yield f"data: {payload}\n\n".encode("utf-8")

                if item.get("type") == "done":
                    break
        finally:
            self.sse_queues.pop(request_id, None)

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
        logger.info(f"[WebChannel] 🌐 本地访问: http://localhost:{port}")
        logger.info(f"[WebChannel] 🌍 服务器访问: http://YOUR_IP:{port} (请将YOUR_IP替换为服务器IP)")
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
            '/stream', 'StreamHandler',
            '/chat', 'ChatHandler',
            '/config', 'ConfigHandler',
            '/api/skills', 'SkillsHandler',
            '/api/memory', 'MemoryHandler',
            '/api/memory/content', 'MemoryContentHandler',
            '/api/scheduler', 'SchedulerHandler',
            '/api/history', 'HistoryHandler',
            '/api/logs', 'LogsHandler',
            '/assets/(.*)', 'AssetsHandler',
        )
        app = web.application(urls, globals(), autoreload=False)
        
        # 完全禁用web.py的HTTP日志输出
        web.httpserver.LogMiddleware.log = lambda self, status, environ: None
        
        # 配置web.py的日志级别为ERROR
        logging.getLogger("web").setLevel(logging.ERROR)
        logging.getLogger("web.httpserver").setLevel(logging.ERROR)
        
        # Build WSGI app with middleware (same as runsimple but without print)
        func = web.httpserver.StaticMiddleware(app.wsgifunc())
        func = web.httpserver.LogMiddleware(func)
        server = web.httpserver.WSGIServer(("0.0.0.0", port), func)
        self._http_server = server
        try:
            server.start()
        except (KeyboardInterrupt, SystemExit):
            server.stop()

    def stop(self):
        if self._http_server:
            try:
                self._http_server.stop()
                logger.info("[WebChannel] HTTP server stopped")
            except Exception as e:
                logger.warning(f"[WebChannel] Error stopping HTTP server: {e}")
            self._http_server = None


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


class StreamHandler:
    def GET(self):
        params = web.input(request_id='')
        request_id = params.request_id
        if not request_id:
            raise web.badrequest()

        web.header('Content-Type', 'text/event-stream; charset=utf-8')
        web.header('Cache-Control', 'no-cache')
        web.header('X-Accel-Buffering', 'no')
        web.header('Access-Control-Allow-Origin', '*')

        return WebChannel().stream_response(request_id)


class ChatHandler:
    def GET(self):
        # 正常返回聊天页面
        file_path = os.path.join(os.path.dirname(__file__), 'chat.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


class ConfigHandler:
    def GET(self):
        """Return configuration info for the web console."""
        try:
            local_config = conf()
            use_agent = local_config.get("agent", False)

            if use_agent:
                title = "CowAgent"
            else:
                title = "AI Assistant"

            return json.dumps({
                "status": "success",
                "use_agent": use_agent,
                "title": title,
                "model": local_config.get("model", ""),
                "channel_type": local_config.get("channel_type", ""),
                "agent_max_context_tokens": local_config.get("agent_max_context_tokens", ""),
                "agent_max_context_turns": local_config.get("agent_max_context_turns", ""),
                "agent_max_steps": local_config.get("agent_max_steps", ""),
            })
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return json.dumps({"status": "error", "message": str(e)})


def _get_workspace_root():
    """Resolve the agent workspace directory."""
    from common.utils import expand_path
    return expand_path(conf().get("agent_workspace", "~/cow"))


class SkillsHandler:
    def GET(self):
        web.header('Content-Type', 'application/json; charset=utf-8')
        try:
            from agent.skills.service import SkillService
            from agent.skills.manager import SkillManager
            workspace_root = _get_workspace_root()
            manager = SkillManager(custom_dir=os.path.join(workspace_root, "skills"))
            service = SkillService(manager)
            skills = service.query()
            return json.dumps({"status": "success", "skills": skills}, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[WebChannel] Skills API error: {e}")
            return json.dumps({"status": "error", "message": str(e)})


class MemoryHandler:
    def GET(self):
        web.header('Content-Type', 'application/json; charset=utf-8')
        try:
            from agent.memory.service import MemoryService
            params = web.input(page='1', page_size='20')
            workspace_root = _get_workspace_root()
            service = MemoryService(workspace_root)
            result = service.list_files(page=int(params.page), page_size=int(params.page_size))
            return json.dumps({"status": "success", **result}, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[WebChannel] Memory API error: {e}")
            return json.dumps({"status": "error", "message": str(e)})


class MemoryContentHandler:
    def GET(self):
        web.header('Content-Type', 'application/json; charset=utf-8')
        try:
            from agent.memory.service import MemoryService
            params = web.input(filename='')
            if not params.filename:
                return json.dumps({"status": "error", "message": "filename required"})
            workspace_root = _get_workspace_root()
            service = MemoryService(workspace_root)
            result = service.get_content(params.filename)
            return json.dumps({"status": "success", **result}, ensure_ascii=False)
        except FileNotFoundError:
            return json.dumps({"status": "error", "message": "file not found"})
        except Exception as e:
            logger.error(f"[WebChannel] Memory content API error: {e}")
            return json.dumps({"status": "error", "message": str(e)})


class SchedulerHandler:
    def GET(self):
        web.header('Content-Type', 'application/json; charset=utf-8')
        try:
            from agent.tools.scheduler.task_store import TaskStore
            workspace_root = _get_workspace_root()
            store_path = os.path.join(workspace_root, "scheduler", "tasks.json")
            store = TaskStore(store_path)
            tasks = store.list_tasks()
            return json.dumps({"status": "success", "tasks": tasks}, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[WebChannel] Scheduler API error: {e}")
            return json.dumps({"status": "error", "message": str(e)})


class HistoryHandler:
    def GET(self):
        """
        Return paginated conversation history for a session.

        Query params:
            session_id  (required)
            page        int, default 1  (1 = most recent messages)
            page_size   int, default 20
        """
        web.header('Content-Type', 'application/json; charset=utf-8')
        web.header('Access-Control-Allow-Origin', '*')
        try:
            params = web.input(session_id='', page='1', page_size='20')
            session_id = params.session_id.strip()
            if not session_id:
                return json.dumps({"status": "error", "message": "session_id required"})

            from agent.memory import get_conversation_store
            store = get_conversation_store()
            result = store.load_history_page(
                session_id=session_id,
                page=int(params.page),
                page_size=int(params.page_size),
            )
            return json.dumps({"status": "success", **result}, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[WebChannel] History API error: {e}")
            return json.dumps({"status": "error", "message": str(e)})


class LogsHandler:
    def GET(self):
        """Stream the last N lines of run.log as SSE, then tail new lines."""
        web.header('Content-Type', 'text/event-stream; charset=utf-8')
        web.header('Cache-Control', 'no-cache')
        web.header('X-Accel-Buffering', 'no')

        from config import get_root
        log_path = os.path.join(get_root(), "run.log")

        def generate():
            if not os.path.isfile(log_path):
                yield b"data: {\"type\": \"error\", \"message\": \"run.log not found\"}\n\n"
                return

            # Read last 200 lines for initial display
            try:
                with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                tail_lines = lines[-200:]
                chunk = ''.join(tail_lines)
                payload = json.dumps({"type": "init", "content": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n".encode('utf-8')
            except Exception as e:
                yield f"data: {{\"type\": \"error\", \"message\": \"{e}\"}}\n\n".encode('utf-8')
                return

            # Tail new lines
            try:
                with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(0, 2)  # seek to end
                    deadline = time.time() + 600  # 10 min max
                    while time.time() < deadline:
                        line = f.readline()
                        if line:
                            payload = json.dumps({"type": "line", "content": line}, ensure_ascii=False)
                            yield f"data: {payload}\n\n".encode('utf-8')
                        else:
                            yield b": keepalive\n\n"
                            time.sleep(1)
            except GeneratorExit:
                return
            except Exception:
                return

        return generate()


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
