import web
import time
import channel.wechatmp.reply as reply
import channel.wechatmp.receive as receive
from config import conf
from common.log import logger
from bridge.context import *
from channel.wechatmp.common import * 
from channel.wechatmp.wechatmp_channel import WechatMPChannel

# This class is instantiated once per query
class Query():

    def GET(self):
        return verify_server(web.input())

    def POST(self):
        # Make sure to return the instance that first created, @singleton will do that. 
        channel_instance = WechatMPChannel()
        try:
            query_time = time.time()
            webData = web.data()
            # logger.debug("[wechatmp] Receive request:\n" + webData.decode("utf-8"))
            wechatmp_msg = receive.parse_xml(webData)
            if wechatmp_msg.msg_type == 'text':
                from_user = wechatmp_msg.from_user_id
                to_user = wechatmp_msg.to_user_id
                message = wechatmp_msg.content.decode("utf-8")
                message_id = wechatmp_msg.msg_id

                logger.info("[wechatmp] {}:{} Receive post query {} {}: {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), from_user, message_id, message))

                cache_key = from_user
                cache = channel_instance.cache_dict.get(cache_key)

                reply_text = ""
                # New request
                if cache == None:
                    # The first query begin, reset the cache
                    channel_instance.cache_dict[cache_key] = (0, "")

                    context = channel_instance._compose_context(ContextType.TEXT, message, isgroup=False, msg=wechatmp_msg)
                    if context:
                        # set private openai_api_key
                        # if from_user is not changed in itchat, this can be placed at chat_channel
                        user_data = conf().get_user_data(from_user)
                        context['openai_api_key'] = user_data.get('openai_api_key') # None or user openai_api_key
                        channel_instance.produce(context)


                    channel_instance.query1[cache_key] = False
                    channel_instance.query2[cache_key] = False
                    channel_instance.query3[cache_key] = False
                # Request again
                elif cache[0] == 0 and channel_instance.query1.get(cache_key) == True and channel_instance.query2.get(cache_key) == True and channel_instance.query3.get(cache_key) == True:
                    channel_instance.query1[cache_key] = False  #To improve waiting experience, this can be set to True.
                    channel_instance.query2[cache_key] = False  #To improve waiting experience, this can be set to True.
                    channel_instance.query3[cache_key] = False
                elif cache[0] >= 1:
                    # Skip the waiting phase
                    channel_instance.query1[cache_key] = True
                    channel_instance.query2[cache_key] = True
                    channel_instance.query3[cache_key] = True


                cache = channel_instance.cache_dict.get(cache_key)
                if channel_instance.query1.get(cache_key) == False:
                    # The first query from wechat official server
                    logger.debug("[wechatmp] query1 {}".format(cache_key))
                    channel_instance.query1[cache_key] = True
                    cnt = 0
                    while cache[0] == 0 and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                        cache = channel_instance.cache_dict.get(cache_key)
                    if cnt == 45:
                        # waiting for timeout (the POST query will be closed by wechat official server)
                        time.sleep(5)
                        # and do nothing
                        return
                    else:
                        pass
                elif channel_instance.query2.get(cache_key) == False:
                    # The second query from wechat official server
                    logger.debug("[wechatmp] query2 {}".format(cache_key))
                    channel_instance.query2[cache_key] = True
                    cnt = 0
                    while cache[0] == 0 and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                        cache = channel_instance.cache_dict.get(cache_key)
                    if cnt == 45:
                        # waiting for timeout (the POST query will be closed by wechat official server)
                        time.sleep(5)
                        # and do nothing
                        return
                    else:
                        pass
                elif channel_instance.query3.get(cache_key) == False:
                    # The third query from wechat official server
                    logger.debug("[wechatmp] query3 {}".format(cache_key))
                    channel_instance.query3[cache_key] = True
                    cnt = 0
                    while cache[0] == 0 and cnt < 45:
                        cnt = cnt + 1
                        time.sleep(0.1)
                        cache = channel_instance.cache_dict.get(cache_key)
                    if cnt == 45:
                        # Have waiting for 3x5 seconds
                        # return timeout message
                        reply_text = "【正在响应中，回复任意文字尝试获取回复】"
                        logger.info("[wechatmp] Three queries has finished For {}: {}".format(from_user, message_id))
                        replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                        return replyPost
                    else:
                        pass

                if float(time.time()) - float(query_time) > 4.8:
                    logger.info("[wechatmp] Timeout for {} {}".format(from_user, message_id))
                    return


                if cache[0] > 1:
                    reply_text = cache[1][:600] + "\n【未完待续，回复任意文字以继续】" #wechatmp auto_reply length limit
                    channel_instance.cache_dict[cache_key] = (cache[0] - 1, cache[1][600:])
                elif cache[0] == 1:
                    reply_text = cache[1]
                    channel_instance.cache_dict.pop(cache_key)
                logger.info("[wechatmp] {}:{} Do send {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), reply_text))
                replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                return replyPost

            elif wechatmp_msg.msg_type == 'event':
                logger.info("[wechatmp] Event {} from {}".format(wechatmp_msg.Event, wechatmp_msg.from_user_id))
                content = subscribe_msg()
                replyMsg = reply.TextMsg(wechatmp_msg.from_user_id, wechatmp_msg.to_user_id, content)
                return replyMsg.send()
            else:
                logger.info("暂且不处理")
                return "success"
        except Exception as exc:
            logger.exception(exc)
            return exc

