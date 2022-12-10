"""
channel factory
"""

from bot.baidu.baidu_unit_bot import BaiduUnitBot
from bot.chatgpt.chat_gpt_bot import ChatGPTBot


def create_bot(bot_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if bot_type == 'baidu':
        return BaiduUnitBot()
    elif bot_type == 'chatGPT':
        return ChatGPTBot()
    raise RuntimeError
