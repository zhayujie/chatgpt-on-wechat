"""
Ollama bot
"""
import json

import requests

from bot.bot import Bot
from bridge.reply import Reply, ReplyType
from common import const
from common.log import logger
from config import conf


class OllamaBot(Bot):
    def __init__(self):
        super().__init__()
        self.base_url = conf().get("ollama", {}).get("base_url", "http://localhost:11434")
        self.model = conf().get("ollama", {}).get("model", "llama2")
        self.api_key = conf().get("ollama", {}).get("api_key", "")

    def reply(self, query, context=None):
        """
        调用Ollama接口生成回复
        :param query: 用户输入的消息
        :param context: 上下文信息
        :return: 回复消息
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # 构建消息历史
            messages = []
            if context and context.get("messages"):
                messages.extend(context.get("messages"))
            messages.append({
                "role": "user",
                "content": query
            })

            # 准备请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }

            # 打印请求信息
            logger.info(f"Ollama API 请求URL: {self.base_url}/api/chat")
            logger.info(f"Ollama API 请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            logger.info(f"Ollama API 请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

            # 发送请求
            response = requests.post(
                f"{self.base_url}/api/chat",
                headers=headers,
                json=data,
                timeout=120
            )

            # 打印响应信息
            logger.info(f"Ollama API 响应状态码: {response.status_code}")
            logger.info(f"Ollama API 响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")

            if response.status_code == 200:
                resp_json = response.json()
                logger.info(f"Ollama API 响应内容: {json.dumps(resp_json, ensure_ascii=False, indent=2)}")
                reply = Reply(
                    ReplyType.TEXT,
                    resp_json.get("message", {}).get("content", "")
                )
                return reply
            else:
                error_msg = f"Ollama API 请求失败，状态码：{response.status_code}, 响应：{response.text}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            logger.error(f"Ollama API 异常：{e}")
            return f"Ollama API 异常：{e}"

    def reply_text(self, query, context=None):
        """
        回复消息，返回文本
        :param query: 用户输入的消息
        :param context: 上下文信息
        :return: 回复消息
        """
        return self.reply(query, context)
