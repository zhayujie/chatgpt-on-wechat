# access LinkAI knowledge base platform
# docs: https://link-ai.tech/platform/link-app/wechat

import time

import requests

from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.openai.open_ai_image import OpenAIImage
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, pconf


class LinkAIBot(Bot):
    # authentication failed
    AUTH_FAILED_CODE = 401
    NO_QUOTA_CODE = 406

    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.args = {}

    def reply(self, query, context: Context = None) -> Reply:
        if context.type == ContextType.TEXT:
            return self._chat(query, context)
        elif context.type == ContextType.IMAGE_CREATE:
            ok, res = self.create_img(query, 0)
            if ok:
                reply = Reply(ReplyType.IMAGE_URL, res)
            else:
                reply = Reply(ReplyType.ERROR, res)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def _chat(self, query, context, retry_count=0) -> Reply:
        """
        发起对话请求
        :param query: 请求提示词
        :param context: 对话上下文
        :param retry_count: 当前递归重试次数
        :return: 回复
        """
        if retry_count >= 2:
            # exit from retry 2 times
            logger.warn("[LINKAI] failed after maximum number of retry times")
            return Reply(ReplyType.ERROR, "请再问我一次吧")

        try:
            # load config
            if context.get("generate_breaked_by"):
                logger.info(f"[LINKAI] won't set appcode because a plugin ({context['generate_breaked_by']}) affected the context")
                app_code = None
            else:
                app_code = context.kwargs.get("app_code") or conf().get("linkai_app_code")
            linkai_api_key = conf().get("linkai_api_key")

            session_id = context["session_id"]

            session = self.sessions.session_query(query, session_id)
            model = conf().get("model") or "gpt-3.5-turbo"
            # remove system message
            if session.messages[0].get("role") == "system":
                if app_code or model == "wenxin":
                    session.messages.pop(0)

            body = {
                "app_code": app_code,
                "messages": session.messages,
                "model": model,     # 对话模型的名称, 支持 gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-4, wenxin, xunfei
                "temperature": conf().get("temperature"),
                "top_p": conf().get("top_p", 1),
                "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            }
            file_id = context.kwargs.get("file_id")
            if file_id:
                body["file_id"] = file_id
            logger.info(f"[LINKAI] query={query}, app_code={app_code}, mode={body.get('model')}, file_id={file_id}")
            headers = {"Authorization": "Bearer " + linkai_api_key}

            # do http request
            base_url = conf().get("linkai_api_base", "https://api.link-ai.chat")
            res = requests.post(url=base_url + "/v1/chat/completions", json=body, headers=headers,
                                timeout=conf().get("request_timeout", 180))
            if res.status_code == 200:
                # execute success
                response = res.json()
                reply_content = response["choices"][0]["message"]["content"]
                total_tokens = response["usage"]["total_tokens"]
                logger.info(f"[LINKAI] reply={reply_content}, total_tokens={total_tokens}")
                self.sessions.session_reply(reply_content, session_id, total_tokens)
    
                agent_suffix = self._fetch_agent_suffix(response)
                if agent_suffix:
                    reply_content += agent_suffix
                if not agent_suffix:
                    knowledge_suffix = self._fetch_knowledge_search_suffix(response)
                    if knowledge_suffix:
                        reply_content += knowledge_suffix
                return Reply(ReplyType.TEXT, reply_content)

            else:
                response = res.json()
                error = response.get("error")
                logger.error(f"[LINKAI] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}")

                if res.status_code >= 500:
                    # server error, need retry
                    time.sleep(2)
                    logger.warn(f"[LINKAI] do retry, times={retry_count}")
                    return self._chat(query, context, retry_count + 1)

                return Reply(ReplyType.ERROR, "提问太快啦，请休息一下再问我吧")

        except Exception as e:
            logger.exception(e)
            # retry
            time.sleep(2)
            logger.warn(f"[LINKAI] do retry, times={retry_count}")
            return self._chat(query, context, retry_count + 1)

    def reply_text(self, session: ChatGPTSession, app_code="", retry_count=0) -> dict:
        if retry_count >= 2:
            # exit from retry 2 times
            logger.warn("[LINKAI] failed after maximum number of retry times")
            return {
                "total_tokens": 0,
                "completion_tokens": 0,
                "content": "请再问我一次吧"
            }

        try:
            body = {
                "app_code": app_code,
                "messages": session.messages,
                "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称, 支持 gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-4, wenxin, xunfei
                "temperature": conf().get("temperature"),
                "top_p": conf().get("top_p", 1),
                "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            }
            if self.args.get("max_tokens"):
                body["max_tokens"] = self.args.get("max_tokens")
            headers = {"Authorization": "Bearer " +  conf().get("linkai_api_key")}

            # do http request
            base_url = conf().get("linkai_api_base", "https://api.link-ai.chat")
            res = requests.post(url=base_url + "/v1/chat/completions", json=body, headers=headers,
                                timeout=conf().get("request_timeout", 180))
            if res.status_code == 200:
                # execute success
                response = res.json()
                reply_content = response["choices"][0]["message"]["content"]
                total_tokens = response["usage"]["total_tokens"]
                logger.info(f"[LINKAI] reply={reply_content}, total_tokens={total_tokens}")
                return {
                    "total_tokens": total_tokens,
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "content": reply_content,
                }

            else:
                response = res.json()
                error = response.get("error")
                logger.error(f"[LINKAI] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}")

                if res.status_code >= 500:
                    # server error, need retry
                    time.sleep(2)
                    logger.warn(f"[LINKAI] do retry, times={retry_count}")
                    return self.reply_text(session, app_code, retry_count + 1)

                return {
                    "total_tokens": 0,
                    "completion_tokens": 0,
                    "content": "提问太快啦，请休息一下再问我吧"
                }

        except Exception as e:
            logger.exception(e)
            # retry
            time.sleep(2)
            logger.warn(f"[LINKAI] do retry, times={retry_count}")
            return self.reply_text(session, app_code, retry_count + 1)


    def create_img(self, query, retry_count=0, api_key=None):
        try:
            logger.info("[LinkImage] image_query={}".format(query))
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {conf().get('linkai_api_key')}"
            }
            data = {
                "prompt": query,
                "n": 1,
                "model": conf().get("text_to_image") or "dall-e-2",
                "response_format": "url",
                "img_proxy": conf().get("image_proxy")
            }
            url = conf().get("linkai_api_base", "https://api.link-ai.chat") + "/v1/images/generations"
            res = requests.post(url, headers=headers, json=data, timeout=(5, 90))
            t2 = time.time()
            image_url = res.json()["data"][0]["url"]
            logger.info("[OPEN_AI] image_url={}".format(image_url))
            return True, image_url

        except Exception as e:
            logger.error(format(e))
            return False, "画图出现问题，请休息一下再问我吧"


    def _fetch_knowledge_search_suffix(self, response) -> str:
        try:
            if response.get("knowledge_base"):
                search_hit = response.get("knowledge_base").get("search_hit")
                first_similarity = response.get("knowledge_base").get("first_similarity")
                logger.info(f"[LINKAI] knowledge base, search_hit={search_hit}, first_similarity={first_similarity}")
                plugin_config = pconf("linkai")
                if plugin_config and plugin_config.get("knowledge_base") and plugin_config.get("knowledge_base").get("search_miss_text_enabled"):
                    search_miss_similarity = plugin_config.get("knowledge_base").get("search_miss_similarity")
                    search_miss_text = plugin_config.get("knowledge_base").get("search_miss_suffix")
                    if not search_hit:
                        return search_miss_text
                    if search_miss_similarity and float(search_miss_similarity) > first_similarity:
                        return search_miss_text
        except Exception as e:
            logger.exception(e)

    def _fetch_agent_suffix(self, response):
        try:
            plugin_list = []
            logger.debug(f"[LinkAgent] res={response}")
            if response.get("agent") and response.get("agent").get("chain") and response.get("agent").get("need_show_plugin"):
                chain = response.get("agent").get("chain")
                suffix = "\n\n- - - - - - - - - - - -"
                i = 0
                for turn in chain:
                    plugin_name = turn.get('plugin_name')
                    suffix += "\n"
                    need_show_thought = response.get("agent").get("need_show_thought")
                    if turn.get("thought") and plugin_name and need_show_thought:
                        suffix += f"{turn.get('thought')}\n"
                    if plugin_name:
                        plugin_list.append(turn.get('plugin_name'))
                        suffix += f"{turn.get('plugin_icon')} {turn.get('plugin_name')}"
                        if turn.get('plugin_input'):
                            suffix += f"：{turn.get('plugin_input')}"
                    if i < len(chain) - 1:
                        suffix += "\n"
                    i += 1
                logger.info(f"[LinkAgent] use plugins: {plugin_list}")
                return suffix
        except Exception as e:
            logger.exception(e)
