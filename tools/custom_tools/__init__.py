from tools.base_tool import BaseTool
from tools.custom_tools.wechat.tool import send_message, send_picture


def _get_wechat_send_message() -> BaseTool:
    return send_message


def _get_wechat_send_picture() -> BaseTool:
    return send_picture


CUSTOM_TOOL = {
    "wechat-send-message": _get_wechat_send_message,
    "wechat-send-picture": _get_wechat_send_picture,
}
