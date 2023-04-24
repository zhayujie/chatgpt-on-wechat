"""
google voice service
"""
import json

import openai

from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from voice.voice import Voice


class OpenaiVoice(Voice):
    def __init__(self):
        openai.api_key = conf().get("open_ai_api_key")

    def voiceToText(self, voice_file):
        logger.debug("[Openai] voice file name={}".format(voice_file))
        try:
            file = open(voice_file, "rb")
            result = openai.Audio.transcribe("whisper-1", file)
            text = result["text"]
            reply = Reply(ReplyType.TEXT, text)
            logger.info("[Openai] voiceToText text={} voice file name={}".format(text, voice_file))
        except Exception as e:
            reply = Reply(ReplyType.ERROR, str(e))
        finally:
            return reply
