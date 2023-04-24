import textwrap

import web
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.utils import check_signature

from config import conf

MAX_UTF8_LEN = 2048


class WeChatAPIException(Exception):
    pass


def verify_server(data):
    try:
        signature = data.signature
        timestamp = data.timestamp
        nonce = data.nonce
        echostr = data.get("echostr", None)
        token = conf().get("wechatmp_token")  # 请按照公众平台官网\基本配置中信息填写
        check_signature(token, signature, timestamp, nonce)
        return echostr
    except InvalidSignatureException:
        raise web.Forbidden("Invalid signature")
    except Exception as e:
        raise web.Forbidden(str(e))


def subscribe_msg():
    trigger_prefix = conf().get("single_chat_prefix", [""])[0]
    msg = textwrap.dedent(
        f"""\
                    感谢您的关注！
                    这里是ChatGPT，可以自由对话。
                    资源有限，回复较慢，请勿着急。
                    支持语音对话。
                    支持图片输入。
                    支持图片输出，画字开头的消息将按要求创作图片。
                    支持tool、角色扮演和文字冒险等丰富的插件。
                    输入'{trigger_prefix}#帮助' 查看详细指令。"""
    )
    return msg
