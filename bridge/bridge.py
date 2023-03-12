from common.log import logger
from bot import bot_factory
from common.singleton import singleton
from voice import voice_factory


@singleton
class Bridge(object):
    def __init__(self):
        self.btype={
            "chat": "chatGPT",
            "voice_to_text": "openai",
            "text_to_voice": "baidu"
        }
        self.bots={}

    def getbot(self,typename):
        if self.bots.get(typename) is None:
            logger.info("create bot {} for {}".format(self.btype[typename],typename))
            if typename == "text_to_voice":
                self.bots[typename] = voice_factory.create_voice(self.btype[typename])
            elif typename == "voice_to_text":
                self.bots[typename] = voice_factory.create_voice(self.btype[typename])
            elif typename == "chat":
                self.bots[typename] = bot_factory.create_bot(self.btype[typename])
        return self.bots[typename]
    
    # 以下所有函数需要得到一个reply字典，格式如下：
    # reply["type"] = "ERROR" / "TEXT" / "VOICE" / ...
    # reply["content"] = reply的内容

    def fetch_reply_content(self, query, context):
        return self.bots["chat"].reply(query, context)

    def fetch_voice_to_text(self, voiceFile):
        return self.bots["voice_to_text"].voiceToText(voiceFile)

    def fetch_text_to_voice(self, text):
        return self.bots["text_to_voice"].textToVoice(text)

