
"""
google voice service
"""
import json
import openai
from config import conf
from common.log import logger
from voice.voice import Voice


class OpenaiVoice(Voice):
    def __init__(self):
        openai.api_key = conf().get('open_ai_api_key')

    def voiceToText(self, voice_file):
        logger.debug(
            '[Openai] voice file name={}'.format(voice_file))
        reply={}
        try:
            file = open(voice_file, "rb")
            result = openai.Audio.transcribe("whisper-1", file)
            text = result["text"]
            reply = {"type": "TEXT", "content": text}
            logger.info(
                '[Openai] voiceToText text={} voice file name={}'.format(text, voice_file))
        except Exception as e:
            reply = {"type": "ERROR", "content": str(e)}
        finally:
            return reply

    def textToVoice(self, text):
        pass
