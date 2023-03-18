from bot import bot_factory
from voice import voice_factory
from config import conf
from common import const


class Bridge(object):
    def __init__(self):
        pass

    def fetch_reply_content(self, query, context):
        bot_type = const.CHATGPT
        model_type = conf().get("model")
        if model_type in ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"]:
            bot_type = const.CHATGPT
        elif model_type in ["text-davinci-003"]:
            bot_type = const.OPEN_AI
        return bot_factory.create_bot(bot_type).reply(query, context)

    def fetch_voice_to_text(self, voiceFile):
        return voice_factory.create_voice("openai").voiceToText(voiceFile)

    def fetch_text_to_voice(self, text):
        return voice_factory.create_voice("baidu").textToVoice(text)