# -*- coding: utf-8 -*-
import web
import time
import math
import hashlib
import textwrap
from channel.channel import Channel
import channel.wechatmp.reply as reply
import channel.wechatmp.receive as receive
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

class WechatMPServer():
    def __init__(self):
        pass

    def startup(self): 
        urls = (
            '/wx', 'WechatMPChannel',
        )
        app = web.application(urls, globals())
        web.httpserver.runsimple(app.wsgifunc(), ('0.0.0.0', 80))

cache_dict = dict()
query1 = dict()
query2 = dict()
query3 = dict()

from concurrent.futures import ThreadPoolExecutor
thread_pool = ThreadPoolExecutor(max_workers=8)

class WechatMPChannel(Channel):

    def GET(self):
        try:
            data = web.input()
            if len(data) == 0:
                return "hello, this is handle view"
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


    def _do_build_reply(self, cache_key, fromUser, message):
        context = dict()
        context['session_id'] = fromUser
        reply_text = super().build_reply_content(message, context)
        # The query is done, record the cache
        logger.info("[threaded] Get reply for {}: {} \nA: {}".format(fromUser, message, reply_text))
        global cache_dict
        reply_cnt = math.ceil(len(reply_text) / 600)
        cache_dict[cache_key] = (reply_cnt, reply_text)


    def send(self, reply : Reply, cache_key):
        global cache_dict
        reply_cnt = math.ceil(len(reply.content) / 600)
        cache_dict[cache_key] = (reply_cnt, reply.content)


    def handle(self, context):
        global cache_dict
        try:
            reply = Reply()
            logger.debug('[wechatmp] ready to handle context: {}'.format(context))

            # reply的构建步骤
            e_context = PluginManager().emit_event(EventContext(Event.ON_HANDLE_CONTEXT, {'channel' : self, 'context': context, 'reply': reply}))
            reply = e_context['reply']
            if not e_context.is_pass():
                logger.debug('[wechatmp] ready to handle context: type={}, content={}'.format(context.type, context.content))
                if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE:
                    reply = super().build_reply_content(context.content, context)
                # elif context.type == ContextType.VOICE:
                #     msg = context['msg']
                #     file_name = TmpDir().path() + context.content
                #     msg.download(file_name)
                #     reply = super().build_voice_to_text(file_name)
                #     if reply.type != ReplyType.ERROR and reply.type != ReplyType.INFO:
                #         context.content = reply.content # 语音转文字后，将文字内容作为新的context
                #         context.type = ContextType.TEXT
                #         reply = super().build_reply_content(context.content, context)
                #         if reply.type == ReplyType.TEXT:
                #             if conf().get('voice_reply_voice'):
                #                 reply = super().build_text_to_voice(reply.content)
                else:
                    logger.error('[wechatmp] unknown context type: {}'.format(context.type))
                    return

            logger.debug('[wechatmp] ready to decorate reply: {}'.format(reply))

            # reply的包装步骤
            if reply and reply.type:
                e_context = PluginManager().emit_event(EventContext(Event.ON_DECORATE_REPLY, {'channel' : self, 'context': context, 'reply': reply}))
                reply=e_context['reply']
                if not e_context.is_pass() and reply and reply.type:
                    if reply.type == ReplyType.TEXT:
                        pass
                    elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
                        reply.content = str(reply.type)+":\n" + reply.content
                    elif reply.type == ReplyType.IMAGE_URL or reply.type == ReplyType.VOICE or reply.type == ReplyType.IMAGE:
                        pass
                    else:
                        logger.error('[wechatmp] unknown reply type: {}'.format(reply.type))
                        return

            # reply的发送步骤
            if reply and reply.type:
                e_context = PluginManager().emit_event(EventContext(Event.ON_SEND_REPLY, {'channel' : self, 'context': context, 'reply': reply}))
                reply=e_context['reply']
                if not e_context.is_pass() and reply and reply.type:
                    logger.debug('[wechatmp] ready to send reply: {} to {}'.format(reply, context['receiver']))
                    self.send(reply, context['receiver'])
            else:
                cache_dict[context['receiver']] = (1, "No reply")

            logger.info("[threaded] Get reply for {}: {} \nA: {}".format(context['receiver'], context.content, reply.content))
        except Exception as exc:
            print(traceback.format_exc())
            cache_dict[context['receiver']] = (1, "ERROR")



    def POST(self):
        try:
            queryTime = time.time()
            webData = web.data()
            # logger.debug("[wechatmp] Receive request:\n" + webData.decode("utf-8"))
            recMsg = receive.parse_xml(webData)
            if isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'text':
                fromUser = recMsg.FromUserName
                toUser = recMsg.ToUserName
                createTime = recMsg.CreateTime
                message = recMsg.Content.decode("utf-8")
                message_id = recMsg.MsgId

                logger.info("[wechatmp] {}:{} Receive post query {} {}: {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), fromUser, message_id, message))

                global cache_dict
                global query1
                global query2
                global query3
                cache_key = fromUser
                cache = cache_dict.get(cache_key)

                reply_text = ""
                # New request
                if cache == None:
                    # The first query begin, reset the cache
                    cache_dict[cache_key] = (0, "")
                    # thread_pool.submit(self._do_build_reply, cache_key, fromUser, message)

                    context = Context()
                    context.kwargs = {'isgroup': False, 'receiver': fromUser, 'session_id': fromUser}

                    user_data = conf().get_user_data(fromUser)
                    context['openai_api_key'] = user_data.get('openai_api_key') # None or user openai_api_key

                    img_match_prefix = check_prefix(message, conf().get('image_create_prefix'))
                    if img_match_prefix:
                        message = message.replace(img_match_prefix, '', 1).strip()
                        context.type = ContextType.IMAGE_CREATE
                    else:
                        context.type = ContextType.TEXT
                    context.content = message
                    thread_pool.submit(self.handle, context)

                    query1[cache_key] = False
                    query2[cache_key] = False
                    query3[cache_key] = False
                # Request again
                elif cache[0] == 0 and query1.get(cache_key) == True and query2.get(cache_key) == True and query3.get(cache_key) == True:
                    query1[cache_key] = False  #To improve waiting experience, this can be set to True.
                    query2[cache_key] = False  #To improve waiting experience, this can be set to True.
                    query3[cache_key] = False
                elif cache[0] >= 1:
                    # Skip the waiting phase
                    query1[cache_key] = True
                    query2[cache_key] = True
                    query3[cache_key] = True


                cache = cache_dict.get(cache_key)
                if query1.get(cache_key) == False:
                    # The first query from wechat official server
                    logger.debug("[wechatmp] query1 {}".format(cache_key))
                    query1[cache_key] = True
                    cnt = 0
                    while cache[0] == 0 and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                        cache = cache_dict.get(cache_key)
                    if cnt == 45:
                        # waiting for timeout (the POST query will be closed by wechat official server)
                        time.sleep(5)
                        # and do nothing
                        return
                    else:
                        pass
                elif query2.get(cache_key) == False:
                    # The second query from wechat official server
                    logger.debug("[wechatmp] query2 {}".format(cache_key))
                    query2[cache_key] = True
                    cnt = 0
                    while cache[0] == 0 and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                        cache = cache_dict.get(cache_key)
                    if cnt == 45:
                        # waiting for timeout (the POST query will be closed by wechat official server)
                        time.sleep(5)
                        # and do nothing
                        return
                    else:
                        pass
                elif query3.get(cache_key) == False:
                    # The third query from wechat official server
                    logger.debug("[wechatmp] query3 {}".format(cache_key))
                    query3[cache_key] = True
                    cnt = 0
                    while cache[0] == 0 and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                        cache = cache_dict.get(cache_key)
                    if cnt == 45:
                        # Have waiting for 3x5 seconds
                        # return timeout message
                        reply_text = "【正在响应中，回复任意文字尝试获取回复】"
                        logger.info("[wechatmp] Three queries has finished For {}: {}".format(fromUser, message_id))
                        replyPost = reply.TextMsg(fromUser, toUser, reply_text).send()
                        return replyPost
                    else:
                        pass

                if float(time.time()) - float(queryTime) > 4.8:
                    logger.info("[wechatmp] Timeout for {} {}".format(fromUser, message_id))
                    return


                if cache[0] > 1:
                    reply_text = cache[1][:600] + "\n【未完待续，回复任意文字以继续】" #wechatmp auto_reply length limit
                    cache_dict[cache_key] = (cache[0] - 1, cache[1][600:])
                elif cache[0] == 1:
                    reply_text = cache[1]
                    cache_dict.pop(cache_key)
                logger.info("[wechatmp] {}:{} Do send {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), reply_text))
                replyPost = reply.TextMsg(fromUser, toUser, reply_text).send()
                return replyPost

            elif isinstance(recMsg, receive.Event) and recMsg.MsgType == 'event':
                logger.info("[wechatmp] Event {} from {}".format(recMsg.Event, recMsg.FromUserName))
                content = textwrap.dedent("""\
                    感谢您的关注！
                    这里是ChatGPT，可以自由对话。
                    资源有限，回复较慢，请勿着急。
                    支持通用表情输入。
                    暂时不支持图片输入。
                    支持图片输出，画字开头的问题将回复图片链接。
                    支持角色扮演和文字冒险两种定制模式对话。
                    输入'#帮助' 查看详细指令。""")
                replyMsg = reply.TextMsg(recMsg.FromUserName, recMsg.ToUserName, content)
                return replyMsg.send()
            else:
                logger.info("暂且不处理")
                return "success"
        except Exception as exc:
            logger.exception(exc)
            return exc


def check_prefix(content, prefix_list):
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return None
