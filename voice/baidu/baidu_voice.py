
"""
baidu voice service
"""
import time
from aip import AipSpeech
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice
from voice.audio_convert import get_pcm_from_wav
from config import conf
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
    填入 config.json 中.
        baidu_app_id: ''
        baidu_api_key: ''
        baidu_secret_key: ''
        baidu_dev_pid: '1536'
"""


class BaiduVoice(Voice):
    APP_ID = conf().get('baidu_app_id')
    API_KEY = conf().get('baidu_api_key')
    SECRET_KEY = conf().get('baidu_secret_key')
    DEV_ID = conf().get('baidu_dev_pid')
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    def __init__(self):
        pass

    def voiceToText(self, voice_file):
        # 识别本地文件
        logger.debug('[Baidu] voice file name={}'.format(voice_file))
        pcm = get_pcm_from_wav(voice_file)
        res = self.client.asr(pcm, "pcm", 16000, {"dev_pid": self.DEV_ID})
        if res["err_no"] == 0:
            logger.info("百度语音识别到了：{}".format(res["result"]))
            text = "".join(res["result"])
            reply = Reply(ReplyType.TEXT, text)
        else:
            logger.info("百度语音识别出错了: {}".format(res["err_msg"]))
            if res["err_msg"] == "request pv too much":
                logger.info("  出现这个原因很可能是你的百度语音服务调用量超出限制，或未开通付费")
            reply = Reply(ReplyType.ERROR,
                          "百度语音识别出错了；{0}".format(res["err_msg"]))
        return reply

    def textToVoice(self, text):
        result = self.client.synthesis(text, 'zh', 1, {
            'spd': 5, 'pit': 5, 'vol': 5, 'per': 111
        })
        if not isinstance(result, dict):
            fileName = TmpDir().path() + '语音回复_' + str(int(time.time())) + '.mp3'
            with open(fileName, 'wb') as f:
                f.write(result)
            logger.info(
                '[Baidu] textToVoice text={} voice file name={}'.format(text, fileName))
            reply = Reply(ReplyType.VOICE, fileName)
        else:
            logger.error('[Baidu] textToVoice error={}'.format(result))
            reply = Reply(ReplyType.ERROR, "抱歉，语音合成失败")
        return reply
