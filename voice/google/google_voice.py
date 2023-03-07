
"""
google voice service
"""

import subprocess
import speech_recognition 
from voice.voice import Voice

class GoogleVoice(Voice):
    recognizer = speech_recognition.Recognizer()

    def __init__(self):
        pass

    def voiceToText(self, voice_file):
        new_file = voice_file.replace('.mp3', '.wav')
        subprocess.call('ffmpeg -i ' + voice_file + ' -acodec pcm_s16le -ac 1 -ar 16000 ' + new_file, shell=True)
        with speech_recognition.AudioFile(new_file) as source:
            audio = self.recognizer.record(source)
        return self.recognizer.recognize_google(audio, language='zh-CN')
