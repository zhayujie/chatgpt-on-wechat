"""
google voice service
"""
import os, json, time

from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from config import conf
from voice.voice import Voice
import requests
from common import const
import datetime, random
from opencc import OpenCC
from openai import OpenAI
from hyaigc import TTS

class OpenaiVoice(Voice):
    def __init__(self):
        self.client = OpenAI(api_key=conf().get("open_ai_api_key"))

    def voiceToText(self, voice_file):
        logger.debug("[Openai] voice file name={}".format(voice_file))
        try:
            audio_file = open(voice_file, "rb")
            result = self.client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            text = result.text
            # 初始化OpenCC，将转换方式设为繁体中文到简体中文
            cc = OpenCC('t2s')
            # 将繁体中文转换为简体中文
            text = cc.convert(text)
            reply = Reply(ReplyType.TEXT, text)
            logger.info("[Openai] voiceToText text={} voice file name={}".format(text, voice_file))
        except Exception as e:
            reply = Reply(ReplyType.ERROR, "我暂时还无法听清您的语音，请稍后再试吧~")
        return reply


    def textToVoice(self, text, retry_count=0):
        try:
            # url = 'https://api.openai.com/v1/audio/speech'
            # headers = {
            #     'Authorization': 'Bearer ' + conf().get("open_ai_api_key"),
            #     'Content-Type': 'application/json'
            # }
            # data = {
            #     'model': conf().get("text_to_voice_model") or const.TTS_1,
            #     'input': text,
            #     'voice': conf().get("tts_voice_id") or "alloy"
            # }
            # response = requests.post(url, headers=headers, json=data)
            # file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
            # logger.debug(f"[OPENAI] text_to_Voice file_name={file_name}, input={text}")
            # with open(file_name, 'wb') as f:
            #     f.write(response.content)
            # logger.info(f"[OPENAI] text_to_Voice success")
            # reply = Reply(ReplyType.VOICE, file_name)

            speech_file_path = TmpDir().path() + "reply-" + str(int(time.time())) + "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"
            logger.info("[Openai] using huya aigc for create speach")
            model = conf().get("text_to_voice_model") or const.TTS_1
            voice = conf().get("tts_voice_id") or "alloy"
            tts = TTS(user='qatest', test=False)
            res = tts.txt2speech(text=text, cdn="OpenAI", model=model, voice=voice, response_format="mp3", speed=1.0)
            with open(speech_file_path, 'wb') as f:
                f.write(res)
            if os.path.exists(speech_file_path):
                logger.info("[Openai] textToVoice text={} voice file name={}".format(text, speech_file_path))
                reply = Reply(ReplyType.VOICE, speech_file_path)
            else:
                # logger.error("[Openai] textToVoice failed ...")
                # reply = Reply(ReplyType.ERROR, "抱歉，语音合成失败")
                raise Exception("textToVoice failed")

        except Exception as e:
            logger.error(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[Openai] textToVoice failed, 第{}次重试".format(retry_count + 1))
                return self.textToVoice(text, retry_count + 1)
            else:
                reply = Reply(ReplyType.ERROR, "遇到了一点小问题，请稍后再问我吧")
        return reply
