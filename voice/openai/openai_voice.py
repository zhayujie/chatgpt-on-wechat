
"""
google voice service
"""
import json
import openai
from common.log import logger
from voice.voice import Voice


class OpenaiVoice(Voice):
    def __init__(self):
        pass

    def voiceToText(self, voice_file):
        file = open(voice_file, "rb")
        reply = openai.Audio.transcribe("whisper-1", file)
        json_dict = json.loads(reply)
        text = json_dict['text']
        logger.info(
            '[Openai] voiceToText text={} voice file name={}'.format(text, voice_file))
        return text

    def textToVoice(self, text):
        pass
