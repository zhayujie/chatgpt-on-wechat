"""
channel factory
"""


def create_bot(bot_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if bot_type == 'baidu':
        # Baidu Unit对话接口
        from bot.baidu.baidu_unit_bot import BaiduUnitBot
        return BaiduUnitBot()

    elif bot_type == 'chatGPT':
        # ChatGPT 网页端web接口
        from bot.chatgpt.chat_gpt_bot import ChatGPTBot
        return ChatGPTBot()

    elif bot_type == 'openAI':
        # OpenAI 官方对话模型API
        from bot.openai.open_ai_bot import OpenAIBot
        return OpenAIBot()
    raise RuntimeError
