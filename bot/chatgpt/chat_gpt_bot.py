# encoding:utf-8

from bot.bot import Bot
from config import conf, load_modes
from common.log import logger
from common.token_bucket import TokenBucket
from common.expired_dict import ExpiredDict
import openai
import time

if conf().get('expires_in_seconds'):
    all_sessions = ExpiredDict(conf().get('expires_in_seconds'))
else:
    all_sessions = dict()
user_mode = dict()
USAGE = \
    "\n用法:\n" \
    "每个人与AI的对话都是单独记忆的, 最多记忆15条问答, 所以不同人之间的对话是独立的\n" \
    "发送 #清除记忆: 清除之前对话记忆\n" \
    "发送 #模式:xx: 切换AI模式, xx为想要的模式, 默认为'chat', 即正常的chatgpt, 'catgirl'为傲娇猫娘, 其他模式正在开发中...\n"


# OpenAI对话模型API (可用)
class ChatGPTBot(Bot):
    def __init__(self):
        openai.api_key = conf().get('open_ai_api_key')
        if conf().get('open_ai_api_base'):
            openai.api_base = conf().get('open_ai_api_base')
        proxy = conf().get('proxy')
        if proxy:
            openai.proxy = proxy
        if conf().get('rate_limit_chatgpt'):
            self.tb4chatgpt = TokenBucket(conf().get('rate_limit_chatgpt', 20))
        if conf().get('rate_limit_dalle'):
            self.tb4dalle = TokenBucket(conf().get('rate_limit_dalle', 50))

    def reply(self, query, context=None, user_name=''):
        # acquire reply content
        print(query, context, user_name)
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            logger.info("[OPEN_AI] query={}".format(query))
            session_id = context.get('session_id') or context.get('from_user_id')
            clear_memory_commands = conf().get('clear_memory_commands', ['#清除记忆'])
            if query.startswith('#模式'):
                quote = ':'
                if '：' in query:
                    quote = '：'
                mode = query.split(quote)[-1]
                modes = load_modes()
                if mode not in modes:
                    return '模式暂不支持'
                if mode == user_mode.get(session_id, None):
                    return f'已经是模式: {mode}'
                else:
                    user_mode[session_id] = mode
                    all_sessions[session_id] = []
                    return f'已经切换到模式: {mode}, 并且清除记忆'
            elif query in clear_memory_commands:
                Session.clear_session(session_id)
                return '记忆已清除'
            elif query == '#清除所有':
                Session.clear_all_session()
                return '所有人记忆已清除'
            elif query == '#更新配置':
                conf()
                return '配置已更新'
            elif query == '#用法':
                return USAGE

            print('here')
            session = Session.build_session_query(query, session_id, user_name)
            logger.debug("[OPEN_AI] session query={}".format(session))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, session_id, 0)
            logger.debug("[OPEN_AI] new_query={}, session_id={}, reply_cont={}".format(session, session_id, reply_content["content"]))
            if reply_content["completion_tokens"] > 0:
                Session.save_session(reply_content["content"], session_id, reply_content["total_tokens"])
            return reply_content["content"]

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_text(self, session, session_id, retry_count=0) -> dict:
        '''
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        '''
        config = conf()
        try:
            if config.get('rate_limit_chatgpt') and not self.tb4chatgpt.get_token():
                return {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
            response = openai.ChatCompletion.create(
                model= config.get("model") or "gpt-3.5-turbo",  # 对话模型的名称
                messages=session,
                temperature=conf().get('temperature', 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
                #max_tokens=4096,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=config.get('frequency_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=config.get('presence_penalty', 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
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
            return {"completion_tokens": 0, "content":"我连接不到你的网络"}
        except openai.error.Timeout as e:
            logger.warn(e)
            logger.warn("[OPEN_AI] Timeout")
            return {"completion_tokens": 0, "content":"我没有收到你的消息"}
        except Exception as e:
            # unknown exception
            logger.exception(e)
            Session.clear_session(session_id)
            return {"completion_tokens": 0, "content": "请再问我一次吧. 有疑问输入#用法 查看帮助"}

    def create_img(self, query, retry_count=0):
        try:
            if conf().get('rate_limit_dalle') and not self.tb4dalle.get_token():
                return "请求太快了，请休息一下再问我吧"
            logger.info("[OPEN_AI] image_query={}".format(query))
            response = openai.Image.create(
                prompt=query,    #图片描述
                n=1,             #每次生成图片的数量
                size="256x256"   #图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response['data'][0]['url']
            logger.info("[OPEN_AI] image_url={}".format(image_url))
            return image_url
        except openai.error.RateLimitError as e:
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.create_img(query, retry_count+1)
            else:
                return "请求太快啦，请休息一下再问我吧"
        except Exception as e:
            logger.exception(e)
            return None

class Session(object):
    @staticmethod
    def build_session_query(query, session_id, user_name=''):
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
        :param user_name: username
        :return: query content with conversaction
        '''
        session = all_sessions.get(session_id, [])
        mode = user_mode.get(session_id, 'chat')
        if len(session) == 0:
            system_prompt = load_modes().get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            all_sessions[session_id] = session
        pre_text = load_modes()[mode]['pre_text']
        if '{}' in pre_text:
            pre_text = pre_text.format(user_name)
        user_item = {'role': 'user', 'content': pre_text + ' ' + query}
        session.append(user_item)
        return session

    @staticmethod
    def save_session(answer, session_id, total_tokens):
        max_tokens = conf().get("conversation_max_tokens")
        if not max_tokens:
            # default 3000
            max_tokens = 1000
        max_tokens = int(max_tokens)

        session = all_sessions.get(session_id)
        if session:
            # append conversation
            gpt_item = {'role': 'assistant', 'content': answer}
            session.append(gpt_item)

        # discard exceed limit conversation
        Session.discard_exceed_conversation(session, max_tokens, total_tokens)
    
    @staticmethod
    def discard_exceed_conversation(session, max_tokens, total_tokens):
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

    @staticmethod
    def clear_session(session_id):
        all_sessions[session_id] = []

    @staticmethod
    def clear_all_session():
        all_sessions.clear()
