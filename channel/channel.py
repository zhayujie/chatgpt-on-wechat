"""
Message sending channel abstract class
"""

from bridge.bridge import Bridge
from bridge.context import Context
from bridge.reply import Reply

class Channel(object):
    def startup(self):
        """
        init channel
        """
        raise NotImplementedError

    def handle_text(self, msg):
        """
        process received msg
        :param msg: message object
        """
        raise NotImplementedError

    def send(self, msg, receiver):
        """
        send message to user
        :param msg: message content
        :param receiver: receiver channel account
        :return: 
        """
        raise NotImplementedError

    def build_reply_content(self, query, context : Context=None) -> Reply:
        return Bridge().fetch_reply_content(query, context)

    def build_voice_to_text(self, voice_file) -> Reply:
        return Bridge().fetch_voice_to_text(voice_file)
    
    def build_text_to_voice(self, text) -> Reply:
        return Bridge().fetch_text_to_voice(text)
