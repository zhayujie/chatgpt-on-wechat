"""
pytts voice service (offline)
"""

import time

import pyttsx3

from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice
import os

class PyttsVoice(Voice):

    def __init__(self):
        self.engine = pyttsx3.init()
        # 语速
        self.engine.setProperty("rate", 125)
        # 音量
        self.engine.setProperty("volume", 1.0)
        for voice in self.engine.getProperty("voices"):
            if "Chinese" in voice.name:
                self.engine.setProperty("voice", voice.id)
        self.engine.setProperty("voice", "zh")
        self.engine.startLoop(useDriverLoop=False)

    def textToVoice(self, text):
        try:
            mp3FileName = "reply-" + str(int(time.time()*100)) + ".mp3"
            mp3File = TmpDir().path() + mp3FileName
            logger.info(
                "[Pytts] textToVoice text={} voice file name={}".format(text, mp3File)
            )
            self.engine.save_to_file(text, mp3File)
            self.engine.iterate()
            while self.engine.isBusy() or mp3FileName not in os.listdir(TmpDir().path()):
                time.sleep(0.1)
            logger.debug("[Pytts] Task finished")
            reply = Reply(ReplyType.VOICE, mp3File)
        except Exception as e:
            print(e)
            reply = Reply(ReplyType.ERROR, str(e))
        finally:
            return reply
