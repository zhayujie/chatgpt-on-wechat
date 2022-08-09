from bot import bot_factory


class Bridge(object):
    def __init__(self):
        pass

    def fetch_reply_content(self, query):
        return bot_factory.BaiduUnitBot().reply(query)
