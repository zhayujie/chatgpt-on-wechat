"""
Voice service abstract class
"""


class Voice(object):
    def voiceToText(self, voice_file):
        """
        Send voice to voice service and get text
        """
        raise NotImplementedError

    def textToVoice(self, text):
        """
        Send text to voice service and get voice
        """
        raise NotImplementedError
