
"""
baidu voice service
"""
import time
from aip import AipSpeech
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice
from config import conf

class BaiduVoice(Voice):
    APP_ID = conf().get('baidu_app_id')
    API_KEY = conf().get('baidu_api_key')
    SECRET_KEY = conf().get('baidu_secret_key')
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    
    def __init__(self):
        pass

    def voiceToText(self, voice_file):
        pass

    def textToVoice(self, text):
        result = self.client.synthesis(text, 'zh', 1, {
            'spd': 5, 'pit': 5, 'vol': 5, 'per': 111
        })
        if not isinstance(result, dict):
            fileName = TmpDir().path() + '语音回复_' + str(int(time.time())) + '.mp3'
            with open(fileName, 'wb') as f:
                f.write(result)
            logger.info('[Baidu] textToVoice text={} voice file name={}'.format(text, fileName))
            return fileName
        else:
            logger.error('[Baidu] textToVoice error={}'.format(result))
            return None
