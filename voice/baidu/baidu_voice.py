"""
baidu voice service
"""
import json
import os
import time

from aip import AipSpeech

from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from config import conf
from voice.audio_convert import get_pcm_from_wav
from voice.voice import Voice

"""
    百度的语音识别API.
    dev_pid:
        - 1936: 普通话远场
        - 1536：普通话(支持简单的英文识别)
        - 1537：普通话(纯中文识别)
        - 1737：英语
        - 1637：粤语
        - 1837：四川话
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    然后在 config.json 中填入这两个值, 以及 app_id, dev_pid
    """


class BaiduVoice(Voice):
    def __init__(self):
        try:
            curdir = os.path.dirname(__file__)
            config_path = os.path.join(curdir, "config.json")
            bconf = None
            if not os.path.exists(config_path):  # 如果没有配置文件，创建本地配置文件
                bconf = {"lang": "zh", "ctp": 1, "spd": 5, "pit": 5, "vol": 5, "per": 0}
                with open(config_path, "w") as fw:
                    json.dump(bconf, fw, indent=4)
            else:
                with open(config_path, "r") as fr:
                    bconf = json.load(fr)

            self.app_id = str(conf().get("baidu_app_id"))
            self.api_key = str(conf().get("baidu_api_key"))
            self.secret_key = str(conf().get("baidu_secret_key"))
            self.dev_id = conf().get("baidu_dev_pid")
            self.lang = bconf["lang"]
            self.ctp = bconf["ctp"]
            self.spd = bconf["spd"]
            self.pit = bconf["pit"]
            self.vol = bconf["vol"]
            self.per = bconf["per"]

            self.client = AipSpeech(self.app_id, self.api_key, self.secret_key)
        except Exception as e:
            logger.warn("BaiduVoice init failed: %s, ignore " % e)

    def voiceToText(self, voice_file):
        # 识别本地文件
        logger.debug("[Baidu] voice file name={}".format(voice_file))
        pcm = get_pcm_from_wav(voice_file)
        res = self.client.asr(pcm, "pcm", 16000, {"dev_pid": self.dev_id})
        if res["err_no"] == 0:
            logger.info("百度语音识别到了：{}".format(res["result"]))
            text = "".join(res["result"])
            reply = Reply(ReplyType.TEXT, text)
        else:
            logger.info("百度语音识别出错了: {}".format(res["err_msg"]))
            if res["err_msg"] == "request pv too much":
                logger.info("  出现这个原因很可能是你的百度语音服务调用量超出限制，或未开通付费")
            reply = Reply(ReplyType.ERROR, "百度语音识别出错了；{0}".format(res["err_msg"]))
        return reply

    def textToVoice(self, text):
        result = self.client.synthesis(
            text,
            self.lang,
            self.ctp,
            {"spd": self.spd, "pit": self.pit, "vol": self.vol, "per": self.per},
        )
        if not isinstance(result, dict):
            # Avoid the same filename under multithreading
            fileName = TmpDir().path() + "reply-" + str(int(time.time())) + "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"
            with open(fileName, "wb") as f:
                f.write(result)
            logger.info("[Baidu] textToVoice text={} voice file name={}".format(text, fileName))
            reply = Reply(ReplyType.VOICE, fileName)
        else:
            logger.error("[Baidu] textToVoice error={}".format(result))
            reply = Reply(ReplyType.ERROR, "抱歉，语音合成失败")
        return reply
