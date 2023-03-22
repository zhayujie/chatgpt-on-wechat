# -*- coding: utf-8 -*-
# filename: main.py
import web
import time
import hashlib
import textwrap
from channel.channel import Channel
import channel.wechatmp.reply as reply
import channel.wechatmp.receive as receive
from common.log import logger
from config import conf


class WechatMPServer():
    def __init__(self):
        pass

    def startup(self):
        urls = (
            '/wx', 'WechatMPChannel',
        )
        app = web.application(urls, globals())
        app.run()


from concurrent.futures import ThreadPoolExecutor
thread_pool = ThreadPoolExecutor(max_workers=8)

cache_dict = dict()
query1 = dict()
query2 = dict()
query3 = dict()

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
        logger.info("[threaded] Get reply_text for {}".format(message))
        global cache_dict
        cache_dict[cache_key] = (1, reply_text)


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

                logger.info("{}:{} [wechatmp] Receive post query {} {}: {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), fromUser, message_id, message))


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
                    thread_pool.submit(self._do_build_reply, cache_key, fromUser, message)
                    query1[cache_key] = False
                    query2[cache_key] = False
                    query3[cache_key] = False
                # Request again
                elif cache[0] == 0 and query1.get(cache_key) == True and query2.get(cache_key) == True and query3.get(cache_key) == True:
                    query1[cache_key] = False
                    query2[cache_key] = False
                    query3[cache_key] = False
                elif cache[0] == 1:
                    reply_text = cache[1]
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
                        reply_text = cache[1]
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
                        reply_text = cache[1]
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
                        reply_text = "服务器有点忙，回复任意文字再次尝试。"
                        logger.info("[wechatmp] Three queries has finished For {}: {}".format(fromUser, message_id))
                        replyPost = reply.TextMsg(fromUser, toUser, reply_text).send()
                        return replyPost
                    else:
                        reply_text = cache[1]

                if float(time.time()) - float(queryTime) > 4.8:
                    logger.info("[wechatmp] Timeout for {} {}".format(fromUser, message_id))
                    return

                cache_dict.pop(cache_key)
                logger.info("{}:{} [wechatmp] Do send {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), reply_text))
                replyPost = reply.TextMsg(fromUser, toUser, reply_text).send()
                return replyPost

            elif isinstance(recMsg, receive.Event) and recMsg.MsgType == 'event':
                toUser = recMsg.FromUserName
                fromUser = recMsg.ToUserName
                content = textwrap.dedent("""\
                    感谢您的关注！
                    这里是ChatGPT。
                    资源有限，回复较慢，请不要着急。
                    """)
                replyMsg = reply.TextMsg(toUser, fromUser, content)
                return replyMsg.send()
            else:
                print("暂且不处理")
                return "success"
        except Exception as Argment:
            print(Argment)
            return Argment
