# encoding:utf-8

import time

import openai
import openai.error
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

            api_key = context.get("openai_api_key")
            model = context.get("gpt_model")
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
                raise openai.error.RateLimitError("RateLimitError: rate limit exceeded")
            # if api_key == None, the default openai.api_key will be used
            if args is None:
                args = self.args
            response = openai.ChatCompletion.create(api_key=api_key, messages=session.messages, **args)
            # logger.debug("[CHATGPT] response={}".format(response))
            # logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {
                "total_tokens": response["usage"]["total_tokens"],
                "completion_tokens": response["usage"]["completion_tokens"],
                "content": response.choices[0]["message"]["content"],
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.error.RateLimitError):
                logger.warn("[CHATGPT] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.error.Timeout):
                logger.warn("[CHATGPT] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIError):
                logger.warn("[CHATGPT] Bad Gateway: {}".format(e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, openai.error.APIConnectionError):
                logger.warn("[CHATGPT] APIConnectionError: {}".format(e))
                result["content"] = "我连接不到你的网络"
                if need_retry:
                    time.sleep(5)
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
        text_to_image_model = conf().get("text_to_image")
        if text_to_image_model == "dall-e-2":
            api_version = "2023-06-01-preview"
            endpoint = conf().get("azure_openai_dalle_api_base","open_ai_api_base")
            # 检查endpoint是否以/结尾
            if not endpoint.endswith("/"):
                endpoint = endpoint + "/"
            url = "{}openai/images/generations:submit?api-version={}".format(endpoint, api_version)
            api_key = conf().get("azure_openai_dalle_api_key","open_ai_api_key")
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            try:
                body = {"prompt": query, "size": conf().get("image_create_size", "256x256"),"n": 1}
                submission = requests.post(url, headers=headers, json=body)
                operation_location = submission.headers['operation-location']
                status = ""
                while (status != "succeeded"):
                    if retry_count > 3:
                        return False, "图片生成失败"
                    response = requests.get(operation_location, headers=headers)
                    status = response.json()['status']
                    retry_count += 1
                image_url = response.json()['result']['data'][0]['url']
                return True, image_url
            except Exception as e:
                logger.error("create image error: {}".format(e))
                return False, "图片生成失败"
        elif text_to_image_model == "dall-e-3":
            api_version = conf().get("azure_api_version", "2024-02-15-preview")
            endpoint = conf().get("azure_openai_dalle_api_base","open_ai_api_base")
            # 检查endpoint是否以/结尾
            if not endpoint.endswith("/"):
                endpoint = endpoint + "/"
            url = "{}openai/deployments/{}/images/generations?api-version={}".format(endpoint, conf().get("azure_openai_dalle_deployment_id","text_to_image"),api_version)
            api_key = conf().get("azure_openai_dalle_api_key","open_ai_api_key")
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            try:
                body = {"prompt": query, "size": conf().get("image_create_size", "1024x1024"), "quality": conf().get("dalle3_image_quality", "standard")}
                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()  # 检查请求是否成功
                data = response.json()

                # 检查响应中是否包含图像 URL
                if 'data' in data and len(data['data']) > 0 and 'url' in data['data'][0]:
                    image_url = data['data'][0]['url']
                    return True, image_url
                else:
                    error_message = "响应中没有图像 URL"
                    logger.error(error_message)
                    return False, "图片生成失败"

            except requests.exceptions.RequestException as e:
                # 捕获所有请求相关的异常
                try:
                    error_detail = response.json().get('error', {}).get('message', str(e))
                except ValueError:
                    error_detail = str(e)
                error_message = f"{error_detail}"
                logger.error(error_message)
                return False, error_message

            except Exception as e:
                # 捕获所有其他异常
                error_message = f"生成图像时发生错误: {e}"
                logger.error(error_message)
                return False, "图片生成失败"
        else:
            return False, "图片生成失败，未配置text_to_image参数"
