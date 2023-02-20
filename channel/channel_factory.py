"""
channel factory
"""

from channel.wechat.wechat_channel import WechatChannel
from channel.wechat.wechaty_channel import WechatyChannel


def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == 'wx':
        return WechatChannel()
    elif channel_type == 'wxy':
        return WechatyChannel()
    raise RuntimeError
