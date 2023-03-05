# encoding:utf-8

from bot.bot import Bot
from config import conf
from common.log import logger
from common.expired_dict import ExpiredDict
import openai
import time

if conf().get('expires_in_seconds'):
    user_session = ExpiredDict(conf().get('expires_in_seconds'))
else:
    user_session = dict()

# OpenAI对话模型API (可用)
class ChatGPTBot(Bot):
    def __init__(self):
        openai.api_key = conf().get('open_ai_api_key')
        proxy = conf().get('proxy')
        if proxy:
            openai.proxy = proxy

    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            logger.info("[OPEN_AI] query={}".format(query))
            from_user_id = context['from_user_id']
            if query == '#清除记忆':
                Session.clear_session(from_user_id)
                return '记忆已清除'
            elif query == '#清除所有':
                Session.clear_all_session()
                return '所有人记忆已清除'            

            new_query = Session.build_session_query(query, from_user_id)
            logger.debug("[OPEN_AI] session query={}".format(new_query))

            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, from_user_id)

            reply_content = self.reply_text(new_query, from_user_id, 0)
            logger.debug("[OPEN_AI] new_query={}, user={}, reply_cont={}".format(new_query, from_user_id, reply_content["content"]))
            if reply_content["completion_tokens"] > 0:
                Session.save_session(reply_content["content"], from_user_id, reply_content["total_tokens"])
            return reply_content["content"]

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_text(self, query, user_id, retry_count=0) ->dict:
        '''
        call openai's ChatCompletion to get the answer
        :param query: query content
        :param user_id: from user id
        :param retry_count: retry count
        :return: {}
        '''
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # 对话模型的名称
                messages=query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                #max_tokens=4096,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            )
            logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {"total_tokens": response["usage"]["total_tokens"], 
                    "completion_tokens": response["usage"]["completion_tokens"], 
                    "content": response.choices[0]['message']['content']}
        except openai.error.RateLimitError as e:
            # rate limit exception
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text(query, user_id, retry_count+1)
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
            Session.clear_session(user_id)
            return {"completion_tokens": 0, "content": "请再问我一次吧"}

    def create_img(self, query, retry_count=0):
        try:
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
                return self.reply_text(query, retry_count+1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            logger.exception(e)
            return None

class Session(object):
    @staticmethod
    def build_session_query(query, user_id):
        '''
        build query with conversation history
        e.g.  [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        ]
        :param query: query content
        :param user_id: from user id
        :return: query content with conversaction
        '''
        session = user_session.get(user_id, [])
        if len(session) == 0:
            system_prompt = conf().get("character_desc", "")
            system_item = {'role': 'system', 'content': system_prompt}
            session.append(system_item)
            user_session[user_id] = session
        user_item = {'role': 'user', 'content': query}
        session.append(user_item)
        return session

    @staticmethod
    def save_session(answer, user_id, total_tokens):
        max_tokens = conf().get("conversation_max_tokens")
        if not max_tokens:
            # default 3000
            max_tokens = 1000
        max_tokens=int(max_tokens)

        session = user_session.get(user_id)
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
    def clear_session(user_id):
        user_session[user_id] = []

    @staticmethod
    def clear_all_session():
        user_session.clear()
