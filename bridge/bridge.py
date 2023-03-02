from bot import bot_factory


class Bridge(object):
    def __init__(self):
        pass

    def fetch_reply_content(self, query, context):
        return bot_factory.create_bot("chatGPT").reply(query, context)
