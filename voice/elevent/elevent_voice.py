"""
eleventLabs voice service

["voice_id":"pNInz6obpgDQGcFmaJgB","name":"Adam"]
["voice_id":"ErXwobaYiN019PkySvjV","name":"Antoni"]
["voice_id":"VR6AewLTigWG4xSOukaG","name":"Arnold"]
["voice_id":"EXAVITQu4vr4xnSDxMaL","name":"Bella"]
["voice_id":"AZnzlk1XvdvUeBnXmlld","name":"Domi"]
["voice_id":"MF3mGyEYCl7XYWbV9V6O","name":"Elli"]
["voice_id":"TxGEqnHWrfWFTfGW9XjX","name":"Josh"]
["voice_id":"21m00Tcm4TlvDq8ikWAM","name":"Rachel"]
["voice_id":"yoZ06aMxZJJ28mfd3POQ","name":"Sam"]

"""

import time
import requests

from elevenlabs import generate

from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice
from config import conf

XI_API_KEY = conf().get("xi_api_key")
name = conf().get("xi_voice_id")

if name == "Adam":
    voice_id = "pNInz6obpgDQGcFmaJgB"
elif name == "Antoni":
    voice_id = "ErXwobaYiN019PkySvjV"
elif name == "Arnold":
    voice_id = "VR6AewLTigWG4xSOukaG"
elif name == "Bella":
    voice_id = "EXAVITQu4vr4xnSDxMaL"
elif name == "Domi":
    voice_id = "AZnzlk1XvdvUeBnXmlld"
elif name == "Elli":
    voice_id = "MF3mGyEYCl7XYWbV9V6O"
elif name == "Josh":
    voice_id = "TxGEqnHWrfWFTfGW9XjX"
elif name == "Rachel":
    voice_id = "21m00Tcm4TlvDq8ikWAM"
elif name == "Sam":
    voice_id = "yoZ06aMxZJJ28mfd3POQ"


class ElevenLabsVoice(Voice):

    def __init__(self):
        pass

    def voiceToText(self, voice_file):
        pass

    def textToVoice(self, text):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": XI_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0,
                "similarity_boost": 0
            }
        }
        response = requests.post(url, json=data, headers=headers)
        audio = response.content
        fileName = TmpDir().path() + "reply-" + str(int(time.time())) + "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"
        with open(fileName, "wb") as f:
            f.write(audio)
        logger.info("[ElevenLabs] textToVoice text={} voice file name={}".format(text, fileName))
        return Reply(ReplyType.VOICE, fileName)