# encoding:utf-8

from bot.bot import Bot
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import conf, load_config
from common.log import logger
from common.token_bucket import TokenBucket
from common.expired_dict import ExpiredDict
import openai
import time


# OpenAI对话模型API (可用)
class ChatGPTBot(Bot):
    def __init__(self):
        openai.api_key = conf().get('open_ai_api_key')
        if conf().get('open_ai_api_base'):
            openai.api_base = conf().get('open_ai_api_base')
        proxy = conf().get('proxy')
        self.sessions = SessionManager()
        if proxy:
            openai.proxy = proxy
        if conf().get('rate_limit_chatgpt'):
            self.tb4chatgpt = TokenBucket(conf().get('rate_limit_chatgpt', 20))
        if conf().get('rate_limit_dalle'):
            self.tb4dalle = TokenBucket(conf().get('rate_limit_dalle', 50))

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[OPEN_AI] query={}".format(query))

            session_id = context['session_id']
            reply = None
            clear_memory_commands = conf().get('clear_memory_commands', ['#清除记忆'])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, '记忆已清除')
            elif query == '#清除所有':
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, '所有人记忆已清除')
            elif query == '#更新配置':
                load_config()
                reply = Reply(ReplyType.INFO, '配置已更新')
            if reply:
                return reply
            session = self.sessions.build_session_query(query, session_id)
            logger.debug("[OPEN_AI] session query={}".format(session))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, session_id, 0)
            logger.debug("[OPEN_AI] new_query={}, session_id={}, reply_cont={}".format(session, session_id, reply_content["content"]))
            if reply_content['completion_tokens'] == 0 and len(reply_content['content']) > 0:
                reply = Reply(ReplyType.ERROR, reply_content['content'])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.save_session(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content['content'])
                logger.debug("[OPEN_AI] reply {} used 0 tokens.".format(reply_content))
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
            reply = Reply(ReplyType.ERROR, 'Bot不支持处理{}类型的消息'.format(context.type))
            return reply

    def compose_args(self):
        return {
            "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
            "temperature":conf().get('temperature', 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # "max_tokens":4096,  # 回复最大的字符数
            "top_p":1,
            "frequency_penalty":conf().get('frequency_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty":conf().get('presence_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        }

    def reply_text(self, session, session_id, retry_count=0) -> dict:
        '''
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        '''
        try:
            if conf().get('rate_limit_chatgpt') and not self.tb4chatgpt.get_token():
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
            response = openai.ChatCompletion.create(
                messages=session, **self.compose_args()
            )
            # logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {"total_tokens": response["usage"]["total_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "content": response.choices[0]['message']['content']}
        except openai.error.RateLimitError as e:
            # rate limit exception
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text(session, session_id, retry_count+1)
            else:
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
        except openai.error.APIConnectionError as e:
            # api connection exception
            logger.warn(e)
            logger.warn("[OPEN_AI] APIConnection failed")
            return {"completion_tokens": 0, "content": "我连接不到你的网络"}
        except openai.error.Timeout as e:
            logger.warn(e)
            logger.warn("[OPEN_AI] Timeout")
            return {"completion_tokens": 0, "content": "我没有收到你的消息"}
        except Exception as e:
            # unknown exception
            logger.exception(e)
            self.sessions.clear_session(session_id)
            return {"completion_tokens": 0, "content": "请再问我一次吧"}

    def create_img(self, query, retry_count=0):
        try:
            if conf().get('rate_limit_dalle') and not self.tb4dalle.get_token():
                return False, "请求太快了，请休息一下再问我吧"
            logger.info("[OPEN_AI] image_query={}".format(query))
            response = openai.Image.create(
                prompt=query,    #图片描述
                n=1,             #每次生成图片的数量
                size="256x256"   #图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response['data'][0]['url']
            logger.info("[OPEN_AI] image_url={}".format(image_url))
            return True, image_url
        except openai.error.RateLimitError as e:
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.create_img(query, retry_count+1)
            else:
                return False, "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            logger.exception(e)
            return False, str(e)


class AzureChatGPTBot(ChatGPTBot):
    def __init__(self):
        super().__init__()
        openai.api_type = "azure"
        openai.api_version = "2023-03-15-preview"

    def compose_args(self):
        args = super().compose_args()
        args["engine"] = args["model"]
        del(args["model"])
        return args


class SessionManager(object):
    def __init__(self):
        if conf().get('expires_in_seconds'):
            sessions = ExpiredDict(conf().get('expires_in_seconds'))
        else:
            sessions = dict()
        self.sessions = sessions

    def build_session(self, session_id, system_prompt=None):
        session = self.sessions.get(session_id, [])
        if len(session) == 0:
            if system_prompt is None:
                system_prompt = conf().get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            self.sessions[session_id] = session
        return session

    def build_session_query(self, query, session_id):
        '''
        build query with conversation history
        e.g.  [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        ]
        :param query: query content
        :param session_id: session id
        :return: query content with conversaction
        '''
        session = self.build_session(session_id)
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        return session

    def save_session(self, answer, session_id, total_tokens):
        max_tokens = conf().get("conversation_max_tokens")
        if not max_tokens:
            # default 3000
            max_tokens = 1000
        max_tokens = int(max_tokens)

        session = self.sessions.get(session_id)
        if session:
            # append conversation
            gpt_item = {'role': 'assistant', 'content': answer}
            session.append(gpt_item)

        # discard exceed limit conversation
        self.discard_exceed_conversation(session, max_tokens, total_tokens)

    def discard_exceed_conversation(self, session, max_tokens, total_tokens):
        dec_tokens = int(total_tokens)
        # logger.info("prompt tokens used={},max_tokens={}".format(used_tokens,max_tokens))
        while dec_tokens > max_tokens:
            # pop first conversation
            if len(session) > 3:
                session.pop(1)
                session.pop(1)
            else:
                break
            dec_tokens = dec_tokens - max_tokens

    def clear_session(self, session_id):
        self.sessions[session_id] = []

    def clear_all_session(self):
        self.sessions.clear()
