from bot import bot_factory
from common.singleton import singleton
from voice import voice_factory


@singleton
class Bridge(object):
    def __init__(self):
        self.bots = {
            "chat": bot_factory.create_bot("chatGPT"),
            "voice_to_text": voice_factory.create_voice("openai"),
            # "text_to_voice": voice_factory.create_voice("baidu")
        }
        try:
            self.bots["text_to_voice"] = voice_factory.create_voice("baidu")
        except ModuleNotFoundError as e:
            print(e)

    # 以下所有函数需要得到一个reply字典，格式如下：
    # reply["type"] = "ERROR" / "TEXT" / "VOICE" / ...
    # reply["content"] = reply的内容

    def fetch_reply_content(self, query, context):
        return self.bots["chat"].reply(query, context)

    def fetch_voice_to_text(self, voiceFile):
        return self.bots["voice_to_text"].voiceToText(voiceFile)

    def fetch_text_to_voice(self, text):
        return self.bots["text_to_voice"].textToVoice(text)
