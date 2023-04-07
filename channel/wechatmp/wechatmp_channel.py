# -*- coding: utf-8 -*-
import web
import time
import math
import hashlib
import textwrap
from channel.chat_channel import ChatChannel
import channel.wechatmp.reply as reply
import channel.wechatmp.receive as receive
from common.expired_dict import ExpiredDict
from common.singleton import singleton
from common.log import logger
from config import conf
from bridge.reply import *
from bridge.context import *
from plugins import *
import traceback

# If using SSL, uncomment the following lines, and modify the certificate path.
# from cheroot.server import HTTPServer
# from cheroot.ssl.builtin import BuiltinSSLAdapter
# HTTPServer.ssl_adapter = BuiltinSSLAdapter(
#         certificate='/ssl/cert.pem',
#         private_key='/ssl/cert.key')


# from concurrent.futures import ThreadPoolExecutor
# thread_pool = ThreadPoolExecutor(max_workers=8)

MAX_UTF8_LEN = 2048
@singleton
class WechatMPChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = [ReplyType.IMAGE, ReplyType.VOICE]
    def __init__(self):
        super().__init__()
        self.cache_dict = dict()
        self.running = set()
        self.query1 = dict()
        self.query2 = dict()
        self.query3 = dict()
        self.received_msgs = ExpiredDict(60*60*24) 

    def startup(self):
        urls = (
            '/wx', 'SubsribeAccountQuery',
        )
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get('wechatmp_port', 8080)
        web.httpserver.runsimple(app.wsgifunc(), ('0.0.0.0', port))


    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        self.cache_dict[receiver] = reply.content
        self.running.remove(receiver)
        logger.debug("[send] reply to {} saved to cache: {}".format(receiver, reply))

    def _fail_callback(self, session_id, exception, context, **kwargs):
        logger.exception("[wechatmp] Fail to generation message to user, msgId={}, exception={}".format(context['msg'].msg_id, exception))
        assert session_id not in self.cache_dict
        self.running.remove(session_id)


def verify_server():
    try:
        data = web.input()
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


# This class is instantiated once per query
class SubsribeAccountQuery():

    def GET(self):
        return verify_server()

    def POST(self):
        channel = WechatMPChannel()
        try:
            query_time = time.time()
            webData = web.data()
            logger.debug("[wechatmp] Receive request:\n" + webData.decode("utf-8"))
            wechat_msg = receive.parse_xml(webData)
            if wechat_msg.msg_type == 'text':
                from_user = wechat_msg.from_user_id
                to_user = wechat_msg.to_user_id
                message = wechat_msg.content.decode("utf-8")
                message_id = wechat_msg.msg_id

                logger.info("[wechatmp] {}:{} Receive post query {} {}: {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), from_user, message_id, message))
                supported = True
                if "【收到不支持的消息类型，暂无法显示】" in message:
                    supported = False # not supported, used to refresh
                cache_key = from_user

                reply_text = ""
                # New request
                if cache_key not in channel.cache_dict and cache_key not in channel.running:
                    # The first query begin, reset the cache
                    context = channel._compose_context(ContextType.TEXT, message, isgroup=False, msg=wechat_msg)
                    logger.debug("[wechatmp] context: {} {}".format(context, wechat_msg))
                    if message_id in channel.received_msgs: # received and finished
                        return 
                    if supported and context:
                        # set private openai_api_key
                        # if from_user is not changed in itchat, this can be placed at chat_channel
                        user_data = conf().get_user_data(from_user)
                        context['openai_api_key'] = user_data.get('openai_api_key') # None or user openai_api_key
                        channel.received_msgs[message_id] = wechat_msg
                        channel.running.add(cache_key)
                        channel.produce(context)
                    else:
                        trigger_prefix = conf().get('single_chat_prefix',[''])[0]
                        if trigger_prefix or not supported:
                            if trigger_prefix:
                                content = textwrap.dedent(f"""\
                                    请输入'{trigger_prefix}'接你想说的话跟我说话。
                                    例如:
                                    {trigger_prefix}你好，很高兴见到你。""")
                            else:
                                content = textwrap.dedent("""\
                                    你好，很高兴见到你。
                                    请跟我说话吧。""")
                        else:
                            logger.error(f"[wechatmp] unknown error")
                            content = textwrap.dedent("""\
                                未知错误，请稍后再试""")
                        replyMsg = reply.TextMsg(wechat_msg.from_user_id, wechat_msg.to_user_id, content)
                        return replyMsg.send()
                    channel.query1[cache_key] = False
                    channel.query2[cache_key] = False
                    channel.query3[cache_key] = False
                # Request again
                elif cache_key in channel.running:
                    channel.query1[cache_key] = False  #To improve waiting experience, this can be set to True.
                    channel.query2[cache_key] = False  #To improve waiting experience, this can be set to True.
                    channel.query3[cache_key] = False
                elif cache_key in channel.cache_dict:
                    # Skip the waiting phase
                    channel.query1[cache_key] = True
                    channel.query2[cache_key] = True
                    channel.query3[cache_key] = True

                assert not (cache_key in channel.cache_dict and cache_key in channel.running)

                if channel.query1.get(cache_key) == False:
                    # The first query from wechat official server
                    logger.debug("[wechatmp] query1 {}".format(cache_key))
                    channel.query1[cache_key] = True
                    cnt = 0
                    while cache_key not in channel.cache_dict and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                    if cnt == 45:
                        # waiting for timeout (the POST query will be closed by wechat official server)
                        time.sleep(1)
                        # and do nothing
                        return
                    else:
                        pass
                elif channel.query2.get(cache_key) == False:
                    # The second query from wechat official server
                    logger.debug("[wechatmp] query2 {}".format(cache_key))
                    channel.query2[cache_key] = True
                    cnt = 0
                    while cache_key not in channel.cache_dict and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                    if cnt == 45:
                        # waiting for timeout (the POST query will be closed by wechat official server)
                        time.sleep(1)
                        # and do nothing
                        return
                    else:
                        pass
                elif channel.query3.get(cache_key) == False:
                    # The third query from wechat official server
                    logger.debug("[wechatmp] query3 {}".format(cache_key))
                    channel.query3[cache_key] = True
                    cnt = 0
                    while cache_key not in channel.cache_dict and cnt < 40:
                        cnt = cnt + 1
                        time.sleep(0.1)
                    if cnt == 40:
                        # Have waiting for 3x5 seconds
                        # return timeout message
                        reply_text = "【正在思考中，回复任意文字尝试获取回复】"
                        logger.info("[wechatmp] Three queries has finished For {}: {}".format(from_user, message_id))
                        replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                        return replyPost
                    else:
                        pass

                if float(time.time()) - float(query_time) > 4.8:
                    reply_text = "【正在思考中，回复任意文字尝试获取回复】"
                    logger.info("[wechatmp] Timeout for {} {}, return".format(from_user, message_id))
                    replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                    return replyPost
                
                if cache_key in channel.cache_dict:
                    content = channel.cache_dict[cache_key]
                    if len(content.encode('utf8'))<=MAX_UTF8_LEN:
                        reply_text = channel.cache_dict[cache_key]
                        channel.cache_dict.pop(cache_key)
                    else:
                        continue_text = "\n【未完待续，回复任意文字以继续】"
                        splits = split_string_by_utf8_length(content, MAX_UTF8_LEN - len(continue_text.encode('utf-8')), max_split= 1)
                        reply_text = splits[0] + continue_text
                        channel.cache_dict[cache_key] = splits[1]
                logger.info("[wechatmp] {}:{} Do send {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), reply_text))
                replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                return replyPost

            elif wechat_msg.msg_type == 'event':
                logger.info("[wechatmp] Event {} from {}".format(wechat_msg.Event, wechat_msg.from_user_id))
                trigger_prefix = conf().get('single_chat_prefix',[''])[0]
                content = textwrap.dedent(f"""\
                    感谢您的关注！
                    这里是ChatGPT，可以自由对话。
                    资源有限，回复较慢，请勿着急。
                    支持通用表情输入。
                    暂时不支持图片输入。
                    支持图片输出，画字开头的问题将回复图片链接。
                    支持角色扮演和文字冒险两种定制模式对话。
                    输入'{trigger_prefix}#帮助' 查看详细指令。""")
                replyMsg = reply.TextMsg(wechat_msg.from_user_id, wechat_msg.to_user_id, content)
                return replyMsg.send()
            else:
                logger.info("暂且不处理")
                return "success"
        except Exception as exc:
            logger.exception(exc)
            return exc

def split_string_by_utf8_length(string, max_length, max_split=0):
    encoded = string.encode('utf-8')
    start, end = 0, 0
    result = []
    while end < len(encoded):
        if max_split > 0 and len(result) >= max_split:
            result.append(encoded[start:].decode('utf-8'))
            break
        end = start + max_length
        # 如果当前字节不是 UTF-8 编码的开始字节，则向前查找直到找到开始字节为止
        while end < len(encoded) and (encoded[end] & 0b11000000) == 0b10000000:
            end -= 1
        result.append(encoded[start:end].decode('utf-8'))
        start = end
    return result