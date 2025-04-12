# cd ../../guymcp 运行uv run server.py --host 127.0.0.1 --port 8020  启动MCP服务器
import time

import openai
# import openai.error
import requests
# # from common import const
# from bot.bot import Bot
# from bot.chatgpt.chat_gpt_session import ChatGPTSession
# from bot.openai.open_ai_image import OpenAIImage
# from bot.session_manager import SessionManager
# from bridge.context import ContextType
# from bridge.reply import Reply, ReplyType
# from common.log import logger
# from common.token_bucket import TokenBucket
# from config import conf, load_config
# from bot.baidu.baidu_wenxin_session import BaiduWenxinSession

import re
# from bot.chatgpt.client import MCPClient
from client import MCPClient
import asyncio


async def gy_getanswer(querystr) -> str:
# guy
    client = MCPClient()
    print("=======>befor call gychat_loop.")
    clean_result = 'null before call gychat_loop.'
    try:
        # server_url =  "http://0.0.0.0:8020/sse" 
        server_url =  "http://127.0.0.1:8020/sse" 
        await client.connect_to_sse_server(server_url)
        # await client.chat_loop()
        res = await client.gychat_loop(querystr)
        print(res)
        clean_result = re.sub(r'\[.*?\]', '', res)

    finally:
        print(f"[****SUCESS call gychat_loop****]: {clean_result}")
        await client.cleanup()
        print("<=======after gychat_loop.")
        print("<=======after cleanup.")
        print(clean_result)
        return clean_result
    
guy_answer = asyncio.run(gy_getanswer('查询张三的电话号码'))
print("guy_answer:",guy_answer)