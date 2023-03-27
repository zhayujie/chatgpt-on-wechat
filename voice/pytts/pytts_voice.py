
"""
pytts voice service (offline)
"""

import time
import pyttsx3
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice


class PyttsVoice(Voice):
    engine = pyttsx3.init()

    def __init__(self):
        # 语速
        self.engine.setProperty('rate', 125)
        # 音量
        self.engine.setProperty('volume', 1.0)
        for voice in self.engine.getProperty('voices'):
            if "Chinese" in voice.name:
                self.engine.setProperty('voice', voice.id)

    def textToVoice(self, text):
        try:
            mp3File = TmpDir().path() + '语音回复_' + str(int(time.time())) + '.mp3'
            self.engine.save_to_file(text, mp3File)
            self.engine.runAndWait()
            logger.info(
                '[Pytts] textToVoice text={} voice file name={}'.format(text, mp3File))
            reply = Reply(ReplyType.VOICE, mp3File)
        except Exception as e:
            reply = Reply(ReplyType.ERROR, str(e))
        finally:
            return reply
