"""
channel factory
"""

def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == 'wx':
        from channel.wechat.wechat_channel import WechatChannel
        return WechatChannel()
    elif channel_type == 'wxy':
        from channel.wechat.wechaty_channel import WechatyChannel
        return WechatyChannel()
    elif channel_type == 'terminal':
        from channel.terminal.terminal_channel import TerminalChannel
        return TerminalChannel()
    elif channel_type == 'wechatmp':
        from channel.wechatmp.wechatmp_channel import WechatMPServer
        return WechatMPServer()
    raise RuntimeError
