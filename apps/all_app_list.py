"""Functionality for loading apps."""
from apps.lite_app import LiteApp
from apps.victorinox import Victorinox
from apps.wechat_roleplay import WechatRolePlay

APP_TO_CLASS = {
    "lite": LiteApp,
    "wechat-roleplay": WechatRolePlay,
    "victorinox": Victorinox
}
