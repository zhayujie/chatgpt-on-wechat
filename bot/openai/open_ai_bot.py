# encoding:utf-8

from bot.bot import Bot
from config import conf
from common.log import logger
import openai
import time

user_session = dict()

# OpenAI对话模型API (可用)
class OpenAIBot(Bot):
    def __init__(self):
        openai.api_key = conf().get('open_ai_api_key')


    def reply(self, query, context=None):
        # acquire reply content
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            logger.info("[OPEN_AI] query={}".format(query))
            from_user_id = context['from_user_id']
            if query == '#清除记忆':
                Session.clear_session(from_user_id)
                return '记忆已清除'

            new_query = Session.build_session_query(query, from_user_id)
            logger.debug("[OPEN_AI] session query={}".format(new_query))

            reply_content = self.reply_text(new_query, from_user_id, 0)
            logger.debug("[OPEN_AI] new_query={}, user={}, reply_cont={}".format(new_query, from_user_id, reply_content))
            if reply_content and query:
                Session.save_session(query, reply_content, from_user_id)
            return reply_content

        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query, 0)

    def reply_text(self, query, user_id, retry_count=0):
        try:
            response = openai.Completion.create(
                model="text-davinci-003",  # 对话模型的名称
                prompt=query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                max_tokens=1200,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["\n\n\n"]
            )
            res_content = response.choices[0]['text'].strip().replace('<|endoftext|>', '')
            logger.info("[OPEN_AI] reply={}".format(res_content))
            return res_content
        except openai.error.RateLimitError as e:
            # rate limit exception
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] RateLimit exceed, 第{}次重试".format(retry_count+1))
                return self.reply_text(query, user_id, retry_count+1)
            else:
                return "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            # unknown exception
            logger.exception(e)
            Session.clear_session(user_id)
            return "请再问我一次吧"


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
        e.g.  Q: xxx
              A: xxx
              Q: xxx
        :param query: query content
        :param user_id: from user id
        :return: query content with conversaction
        '''
        prompt = conf().get("character_desc", "")
        if prompt:
            prompt += "<|endoftext|>\n\n\n"
        session = user_session.get(user_id, None)
        if session:
            for conversation in session:
                prompt += "Q: " + conversation["question"] + "\n\n\nA: " + conversation["answer"] + "<|endoftext|>\n"
            prompt += "Q: " + query + "\nA: "
            return prompt
        else:
            return prompt + "Q: " + query + "\nA: "

    @staticmethod
    def save_session(query, answer, user_id):
        max_tokens = conf().get("conversation_max_tokens")
        if not max_tokens:
            # default 3000
            max_tokens = 1000
        conversation = dict()
        conversation["question"] = query
        conversation["answer"] = answer
        session = user_session.get(user_id)
        logger.debug(conversation)
        logger.debug(session)
        if session:
            # append conversation
            session.append(conversation)
        else:
            # create session
            queue = list()
            queue.append(conversation)
            user_session[user_id] = queue

        # discard exceed limit conversation
        Session.discard_exceed_conversation(user_session[user_id], max_tokens)


    @staticmethod
    def discard_exceed_conversation(session, max_tokens):
        count = 0
        count_list = list()
        for i in range(len(session)-1, -1, -1):
            # count tokens of conversation list
            history_conv = session[i]
            count += len(history_conv["question"]) + len(history_conv["answer"])
            count_list.append(count)

        for c in count_list:
            if c > max_tokens:
                # pop first conversation
                session.pop(0)

    @staticmethod
    def clear_session(user_id):
        user_session[user_id] = []
