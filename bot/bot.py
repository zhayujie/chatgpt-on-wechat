"""
Auto-replay chat robot abstract class
"""


class Bot(object):
    def reply(self, query, context=None):
        """
        bot auto-reply content
        :param req: received message
        :return: reply content
        """
        raise NotImplementedError
