from config import conf
import hashlib
import textwrap


class WeChatAPIException(Exception):
    pass

def verify_server(data):
    try:
        if len(data) == 0:
            return "None"
        signature = data.signature
        timestamp = data.timestamp
        nonce = data.nonce
        echostr = data.echostr
        token = conf().get('wechatmp_token') #请按照公众平台官网\基本配置中信息填写

        data_list = [token, timestamp, nonce]
        data_list.sort()
        sha1 = hashlib.sha1()
        # map(sha1.update, data_list) #python2
        sha1.update("".join(data_list).encode('utf-8'))
        hashcode = sha1.hexdigest()
        print("handle/GET func: hashcode, signature: ", hashcode, signature)
        if hashcode == signature:
            return echostr
        else:
            return ""
    except Exception as Argument:
        return Argument

def subscribe_msg():
    msg = textwrap.dedent("""\
                    感谢您的关注！
                    这里是ChatGPT，可以自由对话。
                    资源有限，回复较慢，请勿着急。
                    支持通用表情输入。
                    暂时不支持图片输入。
                    支持图片输出，画字开头的问题将回复图片或链接。
                    支持角色扮演和文字冒险两种定制模式对话。
                    输入'#帮助' 查看详细指令。""")
    return msg