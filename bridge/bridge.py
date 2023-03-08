from bot import bot_factory
from voice import voice_factory


class Bridge(object):
    def __init__(self):
        pass

    def fetch_reply_content(self, query, context):
        return bot_factory.create_bot("chatGPT").reply(query, context)

    def fetch_voice_to_text(self, voiceFile):
        return voice_factory.create_voice("openai").voiceToText(voiceFile)

    def fetch_text_to_voice(self, text):
        return voice_factory.create_voice("baidu").textToVoice(text)