# encoding:utf-8

import time
import json
import openai
import openai.error
from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config
from .modelscope_session import ModelScopeSession
import requests


# ModelScope对话模型API
class ModelScopeBot(Bot):
    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(ModelScopeSession, model=conf().get("model") or "Qwen/Qwen2.5-7B-Instruct")
        model = conf().get("model") or "Qwen/Qwen2.5-7B-Instruct"
        if model == "modelscope":
            model = "Qwen/Qwen2.5-7B-Instruct"
        self.args = {
            "model": model,  # 对话模型的名称
            "temperature": conf().get("temperature", 0.3),  # 如果设置，值域须为 [0, 1] 我们推荐 0.3，以达到较合适的效果。
            "top_p": conf().get("top_p", 1.0),  # 使用默认值
        }
        self.api_key = conf().get("modelscope_api_key")
        self.base_url = conf().get("modelscope_base_url", "https://api-inference.modelscope.cn/v1/chat/completions")
        """
        需要获取ModelScope支持API-inference的模型名称列表，请到魔搭社区官网模型中心查看 https://modelscope.cn/models?filter=inference_type&page=1。
        或者使用命令 curl https://api-inference.modelscope.cn/v1/models 对模型列表和ID进行获取。查看commend/const.py文件也可以获取模型列表。
        获取ModelScope的免费API Key，请到魔搭社区官网用户中心查看获取方式 https://modelscope.cn/docs/model-service/API-Inference/intro。
        """
    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[MODELSCOPE_AI] query={}".format(query))

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
            logger.debug("[MODELSCOPE_AI] session query={}".format(session.messages))

            model = context.get("modelscope_model")
            new_args = self.args.copy()
            if model:
                new_args["model"] = model

            if new_args["model"] == "Qwen/QwQ-32B":
                reply_content = self.reply_text_stream(session, args=new_args)
            else:
                reply_content = self.reply_text(session, args=new_args)

            logger.debug(
                "[MODELSCOPE_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                # 只有当 content 为空且 completion_tokens 为 0 时才标记为错误
                if len(reply_content["content"]) == 0:
                    reply = Reply(ReplyType.ERROR, reply_content["content"])
                else:
                    reply = Reply(ReplyType.TEXT, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[MODELSCOPE_AI] reply {} used 0 tokens.".format(reply_content))
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

    def reply_text(self, session: ModelScopeSession, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key
            }
            
            body = args
            body["messages"] = session.messages
            res = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(body)
            )

            if res.status_code == 200:
                response = res.json()
                return {
                    "total_tokens": response["usage"]["total_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "content": response["choices"][0]["message"]["content"]
                }
            else:
                response = res.json()
                if "errors" in response:
                    error = response.get("errors")
                elif "error" in response:
                    error = response.get("error")
                else:
                    error = "Unknown error"
                logger.error(f"[MODELSCOPE_AI] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}")

                result = {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
                need_retry = False
                if res.status_code >= 500:
                    # server error, need retry
                    logger.warn(f"[MODELSCOPE_AI] do retry, times={retry_count}")
                    need_retry = retry_count < 2
                elif res.status_code == 401:
                    result["content"] = "授权失败，请检查API Key是否正确"
                elif res.status_code == 429:
                    result["content"] = "请求过于频繁，请稍后再试"
                    need_retry = retry_count < 2
                else:
                    need_retry = False

                if need_retry:
                    time.sleep(3)
                    return self.reply_text(session, args, retry_count + 1)
                else:
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if need_retry:
                return self.reply_text(session, args, retry_count + 1)
            else:
                return result

    def reply_text_stream(self, session: ModelScopeSession, args=None, retry_count=0) -> dict:
        """
        call ModelScope's ChatCompletion to get the answer with stream response
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key
            }
            
            body = args
            body["messages"] = session.messages
            body["stream"] = True  # 启用流式响应

            res = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(body),
                stream=True
            )
            if res.status_code == 200:
                content = ""
                for line in res.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            try:
                                json_data = json.loads(decoded_line[6:])
                                delta_content = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if delta_content:
                                    content += delta_content
                            except json.JSONDecodeError as e:
                                pass
                return {
                    "total_tokens": 1,  # 流式响应通常不返回token使用情况
                    "completion_tokens": 1,
                    "content": content
                }
            else:
                response = res.json()
                if "errors" in response:
                    error = response.get("errors")
                elif "error" in response:
                    error = response.get("error")
                else:
                    error = "Unknown error"
                logger.error(f"[MODELSCOPE_AI] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}")

                result = {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
                need_retry = False
                if res.status_code >= 500:
                    # server error, need retry
                    logger.warn(f"[MODELSCOPE_AI] do retry, times={retry_count}")
                    need_retry = retry_count < 2
                elif res.status_code == 401:
                    result["content"] = "授权失败，请检查API Key是否正确"
                elif res.status_code == 429:
                    result["content"] = "请求过于频繁，请稍后再试"
                    need_retry = retry_count < 2
                else:
                    need_retry = False

                if need_retry:
                    time.sleep(3)
                    return self.reply_text_stream(session, args, retry_count + 1)
                else:
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if need_retry:
                return self.reply_text_stream(session, args, retry_count + 1)
            else:
                return result
    def create_img(self, query, retry_count=0):
        try:
            logger.info("[ModelScopeImage] image_query={}".format(query))
            headers = {
                "Content-Type": "application/json; charset=utf-8",  # 明确指定编码
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "prompt": query,  # required
                "n": 1,
                "model": conf().get("text_to_image"),
            }
            url = "https://api-inference.modelscope.cn/v1/images/generations"
            
            # 手动序列化并保留中文（禁用 ASCII 转义）
            json_payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            
            # 使用 data 参数发送原始字符串（requests 会自动处理编码）
            res = requests.post(url, headers=headers, data=json_payload)
            
            response_data = res.json()
            image_url = response_data['images'][0]['url']
            logger.info("[ModelScopeImage] image_url={}".format(image_url))
            return True, image_url

        except Exception as e:
            logger.error(format(e))
            return False, "画图出现问题，请休息一下再问我吧"