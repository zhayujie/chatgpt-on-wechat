
"""
baidu voice service
"""
from aip import AipSpeech
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
        pass
