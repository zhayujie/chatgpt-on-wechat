"""
channel factory
"""

from channel.wechat.wechat_channel import WechatChannel
from channel.gmail.gmail_channel import GmailChannel

def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == 'wx':
        return WechatChannel()
    if channel_type == 'gmail':
        return GmailChannel()
    raise RuntimeError