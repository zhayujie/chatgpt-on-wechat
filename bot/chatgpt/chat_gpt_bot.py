# encoding:utf-8

import time
import json

import openai
import requests

from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.openai.open_ai_image import OpenAIImage
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.token_bucket import TokenBucket
from config import conf, load_config

from hyaigc import ChatCompletion
from scripts import function as fun


# OpenAI对话模型API (可用)
class ChatGPTBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        # set the default api_key
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("open_ai_api_base"):
            openai.api_base = conf().get("open_ai_api_base")
        proxy = conf().get("proxy")
        if proxy:
            openai.proxy = proxy
        if conf().get("rate_limit_chatgpt"):
            self.tb4chatgpt = TokenBucket(conf().get("rate_limit_chatgpt", 20))

        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.args = {
            "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # "max_tokens":4096,  # 回复最大的字符数
            "top_p": conf().get("top_p", 1),
            "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }

        self.alapi_key = conf().get("alapi_key", None)
        self.bing_subscription_key = conf().get("bing_subscription_key", None)
        self.app_key = conf().get("app_key", None)
        self.app_sign = conf().get("app_sign", None)

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[CHATGPT] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[CHATGPT] session query={}".format(session.messages))

            api_key = conf().get("open_ai_api_key", "")
            model = conf().get('model') or "gpt-4"
            new_args = None
            if model:
                new_args = self.args.copy()
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, api_key, args=new_args)
            logger.debug(
                "[CHATGPT] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[CHATGPT] reply {} used 0 tokens.".format(reply_content))
            return reply

        elif context.type == ContextType.IMAGE_CREATE:
            ok, retstring = self.create_img(query, 0)
            reply = None
            if ok:
                reply = Reply(ReplyType.IMAGE_URL, retstring)
            else:
                reply = Reply(ReplyType.ERROR, retstring)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: ChatGPTSession, api_key=None, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            if conf().get("rate_limit_chatgpt") and not self.tb4chatgpt.get_token():
                raise openai.OpenAIError("RateLimitError: rate limit exceeded")
            # if api_key == None, the default openai.api_key will be used

            functions = [
                {
                    "name": "get_current_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "Cities with Chinese names, for example: 广州, 深圳",
                            },
                        },
                        "required": ["city"],
                    },
                },
                {
                    "name": "get_morning_news",
                    "description": "获取新闻早报",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_hotlist",
                    "description": "获取各种热榜信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "type类型: '知乎':zhihu', '微博':weibo', '微信':weixin', '百度':baidu', '头条':toutiao', '163':163', 'xl', '36氪':36k', 'hitory', 'sspai', 'csdn', 'juejin', 'bilibili', 'douyin', '52pojie', 'v2ex', 'hostloc'",
                            }
                        },
                        "required": ["type"],
                    }
                },
                {
                    "name": "search_bing",
                    "description": "必应搜索引擎，本函数需要有明确包含'搜索'的指令内容才可以调用",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "提供需要搜索的关键词信息",
                            },
                            "count": {
                                "type": "string",
                                "description": "搜索页数,如无指定几页，默认3",
                            }

                        },
                        "required": ["query", "count"],
                    },
                },
                {
                    "name": "get_oil_price",
                    "description": "获取全国油价信息",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_Constellation_analysis",
                    "description": "获取星座运势",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "star": {
                                "type": "string",
                                "description": """星座英文        
                                                            "白羊座": "aries",
                                                            "金牛座": "taurus",
                                                            "双子座": "gemini",
                                                            "巨蟹座": "cancer",
                                                            "狮子座": "leo",
                                                            "处女座": "virgo",
                                                            "天秤座": "libra",
                                                            "天蝎座": "scorpio",
                                                            "射手座": "sagittarius",
                                                            "摩羯座": "capricorn",
                                                            "水瓶座": "aquarius",
                                                            "双鱼座": "pisces"""
                            },

                        },
                        "required": ["star"],
                    },
                },
                {
                    "name": "music_search",
                    "description": "音乐搜索，获得音乐信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "需要搜索的音乐关键词信息",
                            },

                        },
                        "required": ["keyword"],
                    },
                },
                {
                    "name": "get_datetime",
                    "description": "获取指定城市实时日期时间和星期信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_en": {
                                "type": "string",
                                "description": "需要查询的城市小写英文名，英文名中间空格用-代替，如beijing，new-york",
                            },

                        },
                        "required": ["city_en"],
                    },
                },
                {
                    "name": "get_url",
                    "description": "获取指定URL的内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "需要访问的指定URL",
                            },

                        },
                        "required": ["url"],
                    },
                },
                {
                    "name": "find_simular_bugs",
                    "description": "Internal research and development or testing use within Huya Company",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The query that the user asks, e.g. 测试有料视频需要注意什么"
                            },
                            "num": {
                                "type": "integer",
                                "description": "The number of items that is desired to return, e.g. 15"
                            }
                        },
                        "required": ["prompt"]
                    }
                },
            ]

            if args is None:
                args = self.args
            # response = openai.ChatCompletion.create(api_key=api_key, messages=session.messages, **args)
            logger.info(f"[CHATGPT] using huya aigc for {args['model']}")
            ai = ChatCompletion(user='qatest', test=False, model=args['model'], cdn='Azure')
            response = ai.chat_raw_msg(cdn="Azure", functions=functions, messages=session.messages, **args)

            message = response["choices"][0]["message"]

            # 检查模型是否希望调用函数
            if message.get("function_call") and not message.get("content"):
                function_name = message["function_call"]["name"]
                logger.debug(f"Function call: {function_name}")  # 打印函数调用
                logger.debug(f"message={message}")
                function_response = ""

                # 处理各种可能的函数调用，执行函数并获取函数的返回结果
                if function_name == "get_current_weather":
                    function_args = json.loads(message["function_call"].get("arguments", "{}"))
                    logger.debug(f"Function arguments: {function_args}")  # 打印函数参数

                    function_response = fun.get_current_weather(api_key=self.alapi_key,
                                                                city=function_args.get("city", "未指定地点"),
                                                                )
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应

                elif function_name == "get_morning_news":
                    function_response = fun.get_morning_news(api_key=self.alapi_key)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应

                elif function_name == "get_hotlist":
                    function_args_str = message["function_call"].get("arguments", "{}")
                    function_args = json.loads(function_args_str)  # 使用 json.loads 将字符串转换为字典
                    hotlist_type = function_args.get("type", "未指定类型")
                    function_response = fun.get_hotlist(api_key=self.alapi_key, type=hotlist_type)
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应

                elif function_name == "search_bing":
                    function_args_str = message["function_call"].get("arguments", "{}")
                    function_args = json.loads(function_args_str)  # 使用 json.loads 将字符串转换为字典
                    search_query = function_args.get("query", "未指定关键词")
                    search_count = function_args.get("count", 3)
                    function_response = fun.search_bing(subscription_key=self.bing_subscription_key,
                                                        query=search_query,
                                                        count=search_count,
                                                        endpoint="https://api.bing.microsoft.com/v7.0/search")
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应
                elif function_name == "get_oil_price":
                    function_response = fun.get_oil_price(api_key=self.alapi_key)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应
                elif function_name == "get_Constellation_analysis":
                    function_args = json.loads(message["function_call"].get("arguments", "{}"))
                    logger.debug(f"Function arguments: {function_args}")  # 打印函数参数

                    function_response = fun.get_Constellation_analysis(api_key=self.alapi_key,
                                                                       star=function_args.get("star", "未指定星座"),
                                                                       )
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应
                elif function_name == "music_search":
                    function_args = json.loads(message["function_call"].get("arguments", "{}"))
                    logger.debug(f"Function arguments: {function_args}")  # 打印函数参数

                    function_response = fun.music_search(api_key=self.alapi_key,
                                                         keyword=function_args.get("keyword", "未指定音乐"),
                                                         )
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应
                elif function_name == "get_datetime":
                    function_args = json.loads(message["function_call"].get("arguments", "{}"))
                    logger.debug(f"Function arguments: {function_args}")  # 打印函数参数
                    city = function_args.get("city_en", "beijing")  # 如果没有指定城市，将默认查询北京
                    function_response = fun.get_datetime(appkey=self.app_key, sign=self.app_sign, city_en=city)
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应
                elif function_name == "get_url":
                    function_args = json.loads(message["function_call"].get("arguments", "{}"))
                    logger.debug(f"Function arguments: {function_args}")  # 打印函数参数
                    url = function_args.get("url", "未指定URL")  # 如果没有指定URL，输入默认文本
                    function_response = fun.get_url(url=url)
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应
                elif function_name == "find_simular_bugs":
                    function_args = json.loads(message["function_call"].get("arguments", "{}"))
                    logger.debug(f"Function arguments: {function_args}")  # 打印函数参数
                    prompt = function_args.get("prompt", "未指定prompt")  # 如果没有指定prompt，输入默认文本
                    num = function_args.get("num", 15)  # 如果没有指定num，将默认检索15条记录
                    function_response = fun.find_simular_bugs(prompt=prompt, num=num)
                    function_response = json.dumps(function_response, ensure_ascii=False)
                    logger.debug(f"Function response: {function_response}")  # 打印函数响应

                # 将函数的返回结果发送给第二个模型
                logger.info(f"[CHATGPT] using huya aigc for {args['model']}")
                session.messages.append(message)
                session.messages.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response
                    }
                )
                second_response = ai.chat_raw_msg(cdn="Azure", functions=functions, messages=session.messages, **args)
                logger.debug(f"Second response: {second_response['choices'][0]['message']['content']}")  # 打印第二次的响应
                return {
                    "total_tokens": second_response["usage"]["total_tokens"],
                    "completion_tokens": second_response["usage"]["completion_tokens"],
                    "content": second_response["choices"][0]["message"]["content"],
                }
            else:
                # 如果模型不希望调用函数，直接打印其响应
                logger.debug(f"Model response: {message['content']}")  # 打印模型的响应
                return {
                    "total_tokens": response["usage"]["total_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "content": response["choices"][0]["message"]["content"],
                }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.RateLimitError):
                logger.warn("[CHATGPT] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.Timeout):
                logger.warn("[CHATGPT] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.APIError):
                logger.warn("[CHATGPT] Bad Gateway: {}".format(e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, openai.APIConnectionError):
                logger.warn("[CHATGPT] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                logger.exception("[CHATGPT] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[CHATGPT] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, api_key, args, retry_count + 1)
            else:
                return result


class AzureChatGPTBot(ChatGPTBot):
    def __init__(self):
        super().__init__()
        openai.api_type = "azure"
        openai.api_version = conf().get("azure_api_version", "2023-06-01-preview")
        self.args["deployment_id"] = conf().get("azure_deployment_id")

    def create_img(self, query, retry_count=0, api_key=None):
        api_version = "2022-08-03-preview"
        url = "{}dalle/text-to-image?api-version={}".format(openai.api_base, api_version)
        api_key = api_key or openai.api_key
        headers = {"api-key": api_key, "Content-Type": "application/json"}
        try:
            body = {"caption": query, "resolution": conf().get("image_create_size", "256x256")}
            submission = requests.post(url, headers=headers, json=body)
            operation_location = submission.headers["Operation-Location"]
            retry_after = submission.headers["Retry-after"]
            status = ""
            image_url = ""
            while status != "Succeeded":
                logger.info("waiting for image create..., " + status + ",retry after " + retry_after + " seconds")
                time.sleep(int(retry_after))
                response = requests.get(operation_location, headers=headers)
                status = response.json()["status"]
            image_url = response.json()["result"]["contentUrl"]
            return True, image_url
        except Exception as e:
            logger.error("create image error: {}".format(e))
            return False, "图片生成失败"
