"""
channel factory
"""
from common import const

def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == "wx":
        from channel.wechat.wechat_channel import WechatChannel

        return WechatChannel()
    elif channel_type == "wxy":
        from channel.wechat.wechaty_channel import WechatyChannel

        return WechatyChannel()
    elif channel_type == "terminal":
        from channel.terminal.terminal_channel import TerminalChannel

        return TerminalChannel()
    elif channel_type == "wechatmp":
        from channel.wechatmp.wechatmp_channel import WechatMPChannel

        return WechatMPChannel(passive_reply=True)
    elif channel_type == "wechatmp_service":
        from channel.wechatmp.wechatmp_channel import WechatMPChannel

        return WechatMPChannel(passive_reply=False)
    elif channel_type == "wechatcom_app":
        from channel.wechatcom.wechatcomapp_channel import WechatComAppChannel

        return WechatComAppChannel()
    elif channel_type == "wework":
        from channel.wework.wework_channel import WeworkChannel
        return WeworkChannel()

    elif channel_type == const.FEISHU:
        from channel.feishu.feishu_channel import FeiShuChanel
        return FeiShuChanel()

    raise RuntimeError
