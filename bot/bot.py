"""
Auto-replay chat robot abstract class
"""


class Bot(object):
    def reply(self, query):
        """
        bot auto-reply content
        :param req: received message
        :return: reply content
        """
        raise NotImplementedError
