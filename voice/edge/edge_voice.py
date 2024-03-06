import time

import edge_tts
import asyncio

from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice
from config import conf


class EdgeVoice(Voice):

    def __init__(self):
        '''
        # 普通话
        zh-CN-XiaoxiaoNeural
        zh-CN-XiaoyiNeural
        zh-CN-YunjianNeural
        zh-CN-YunxiNeural
        zh-CN-YunxiaNeural
        zh-CN-YunyangNeural
        # 地方口音
        zh-CN-liaoning-XiaobeiNeural
        zh-CN-shaanxi-XiaoniNeural
        # 粤语
        zh-HK-HiuGaaiNeural
        zh-HK-HiuMaanNeural
        zh-HK-WanLungNeural
        # 湾湾腔
        zh-TW-HsiaoChenNeural
        zh-TW-HsiaoYuNeural
        zh-TW-YunJheNeural
        '''
        self.voice = conf().get("voicespecies")
        # self.voice = "zh-CN-liaoning-XiaobeiNeural"

    def voiceToText(self, voice_file):
        pass

    async def gen_voice(self, text, fileName):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(fileName)

    def textToVoice(self, text):
        self.voice = conf().get("voicespecies")
        fileName = TmpDir().path() + "reply-" + str(int(time.time())) + "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"

        asyncio.run(self.gen_voice(text, fileName))
        logger.info(f"[EdgeTTS] textToVoice voicespecies: {self.voice}")
        logger.debug("[EdgeTTS] textToVoice text={} voice file name={}".format(text, fileName))
        return Reply(ReplyType.VOICE, fileName)