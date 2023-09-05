# http_server.py
import os
import time
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from common.log import logger
message_handlers = []


def register_handler(func):
    message_handlers.append(func)
    return func


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            raw_message = body.decode()
            message = json.loads(raw_message)
            logger.debug(f"http服务接收到信息：{message}")
            for handler in message_handlers:
                handler(message)
            self.send_response(200)
        except Exception as e:
            traceback.print_exc()  # 打印完整的堆栈跟踪
            self.send_response(500)
        finally:
            self.end_headers()


def run_server(port=8001):
    httpd = HTTPServer(('localhost', port), MyHTTPRequestHandler)
    httpd.serve_forever()


def forever():
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        os._exit(0)
