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
