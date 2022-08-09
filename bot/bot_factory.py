"""
channel factory
"""

from bot.baidu.baidu_unit_bot import BaiduUnitBot


def create_bot(bot_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if bot_type == 'baidu':
        return BaiduUnitBot()
    raise RuntimeError