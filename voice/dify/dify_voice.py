import os
import requests
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from voice.voice import Voice
from voice.audio_convert import any_to_mp3
import datetime
import random

class DifyVoice(Voice):
    def voiceToText(self, voice_file):
        logger.debug("[DIFY VOICE] voice file name={}".format(voice_file))
        try:
            # 测试发现dify不支持wav格式，支持mp3格式，统一转为mp3格式
            filepath, ext = os.path.splitext(voice_file)
            if ext != ".mp3":
                old_voice_file = voice_file
                voice_file = filepath + ".mp3"
                if os.path.exists(old_voice_file):
                    any_to_mp3(old_voice_file, voice_file)
            files = {
                'file': (os.path.basename(voice_file), open(voice_file, 'rb'), 'audio/mp3')
            }
            headers = {
                'Authorization': 'Bearer ' + conf().get("dify_api_key")
            }
            response = requests.post(
                f'{conf().get("dify_api_base")}/audio-to-text',
                headers=headers,
                files=files
            )
            if response.status_code != 200:
                logger.error(response.text)
                response.raise_for_status()
            response_data = response.json()
            text = response_data['text']
            reply = Reply(ReplyType.TEXT, text)
            logger.info("[DIFY VOICE] voiceToText text={} voice file name={}".format(text, voice_file))
        except Exception as e:
            logger.error(f"[DIFY VOICE] voiceToText error={e}")
            reply = Reply(ReplyType.ERROR, "我暂时还无法听清您的语音，请稍后再试吧~")
        return reply

    def textToVoice(self, text):
        logger.debug("[DIFY VOICE] text={}".format(text))
        try:
            data = {
                'text': text
            }
            headers = {
                'Authorization': 'Bearer ' + conf().get("dify_api_key")
            }
            #TODO: raise and log response
            response = requests.post(
                f'{conf().get("dify_api_base")}/text-to-audio',
                headers=headers,
                json=data
            )
            file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
            with open(file_name, 'wb') as f:
                f.write(response.content)
            logger.info("[DIFY VOICE] textToVoice success, file_name={}".format(file_name))
            reply = Reply(ReplyType.VOICE, file_name)
        except Exception as e:
            logger.error(e)
            reply = Reply(ReplyType.ERROR, "遇到了一点小问题，请稍后再问我吧")
        return reply
