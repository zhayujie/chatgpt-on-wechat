"""
channel factory
"""
from common import const


def create_bot(bot_type):
    """
    create a bot_type instance
    :param bot_type: bot type code
    :return: bot instance
    """
    if bot_type == const.BAIDU:
        # Baidu Unit对话接口
        from bot.baidu.baidu_unit_bot import BaiduUnitBot

        return BaiduUnitBot()

    elif bot_type == const.CHATGPT:
        # ChatGPT 网页端web接口
        from bot.chatgpt.chat_gpt_bot import ChatGPTBot

        return ChatGPTBot()

    elif bot_type == const.OPEN_AI:
        # OpenAI 官方对话模型API
        from bot.openai.open_ai_bot import OpenAIBot

        return OpenAIBot()

    elif bot_type == const.CHATGPTONAZURE:
        # Azure chatgpt service https://azure.microsoft.com/en-in/products/cognitive-services/openai-service/
        from bot.chatgpt.chat_gpt_bot import AzureChatGPTBot

        return AzureChatGPTBot()

    elif bot_type == const.LINKAI:
        from bot.linkai.link_ai_bot import LinkAIBot
        return LinkAIBot()

    raise RuntimeError
