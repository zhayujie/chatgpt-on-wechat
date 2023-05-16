"""
eleventLabs voice service
"""

import time

from elevenlabs import generate

from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice


class ElevenLabsVoice(Voice):

    def __init__(self):
        pass

    def voiceToText(self, voice_file):
        pass

    def textToVoice(self, text):
        audio = generate(
            text=text
        )
        fileName = TmpDir().path() + "reply-" + str(int(time.time())) + "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"
        with open(fileName, "wb") as f:
            f.write(audio)
        logger.info("[ElevenLabs] textToVoice text={} voice file name={}".format(text, fileName))
        return Reply(ReplyType.VOICE, fileName)

