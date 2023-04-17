import time

import web

import channel.wechatmp.receive as receive
import channel.wechatmp.reply as reply
from bridge.context import *
from channel.wechatmp.common import *
from channel.wechatmp.wechatmp_channel import WechatMPChannel
from common.log import logger
from config import conf


# This class is instantiated once per query
class Query:
    def GET(self):
        return verify_server(web.input())

    def POST(self):
        # Make sure to return the instance that first created, @singleton will do that.
        channel = WechatMPChannel()
        try:
            query_time = time.time()
            webData = web.data()
            logger.debug("[wechatmp] Receive request:\n" + webData.decode("utf-8"))
            wechatmp_msg = receive.parse_xml(webData)
            if wechatmp_msg.msg_type == "text" or wechatmp_msg.msg_type == "voice":
                from_user = wechatmp_msg.from_user_id
                to_user = wechatmp_msg.to_user_id
                message = wechatmp_msg.content.decode("utf-8")
                message_id = wechatmp_msg.msg_id

                logger.info(
                    "[wechatmp] {}:{} Receive post query {} {}: {}".format(
                        web.ctx.env.get("REMOTE_ADDR"),
                        web.ctx.env.get("REMOTE_PORT"),
                        from_user,
                        message_id,
                        message,
                    )
                )
                supported = True
                if "【收到不支持的消息类型，暂无法显示】" in message:
                    supported = False  # not supported, used to refresh
                cache_key = from_user

                reply_text = ""
                # New request
                if (
                    cache_key not in channel.cache_dict
                    and cache_key not in channel.running
                ):
                    # The first query begin, reset the cache
                    context = channel._compose_context(
                        ContextType.TEXT, message, isgroup=False, msg=wechatmp_msg
                    )
                    logger.debug(
                        "[wechatmp] context: {} {}".format(context, wechatmp_msg)
                    )
                    if message_id in channel.received_msgs:  # received and finished
                        # no return because of bandwords or other reasons
                        return "success"
                    if supported and context:
                        # set private openai_api_key
                        # if from_user is not changed in itchat, this can be placed at chat_channel
                        user_data = conf().get_user_data(from_user)
                        context["openai_api_key"] = user_data.get(
                            "openai_api_key"
                        )  # None or user openai_api_key
                        channel.received_msgs[message_id] = wechatmp_msg
                        channel.running.add(cache_key)
                        channel.produce(context)
                    else:
                        trigger_prefix = conf().get("single_chat_prefix", [""])[0]
                        if trigger_prefix or not supported:
                            if trigger_prefix:
                                content = textwrap.dedent(
                                    f"""\
                                    请输入'{trigger_prefix}'接你想说的话跟我说话。
                                    例如:
                                    {trigger_prefix}你好，很高兴见到你。"""
                                )
                            else:
                                content = textwrap.dedent(
                                    """\
                                    你好，很高兴见到你。
                                    请跟我说话吧。"""
                                )
                        else:
                            logger.error(f"[wechatmp] unknown error")
                            content = textwrap.dedent(
                                """\
                                未知错误，请稍后再试"""
                            )
                        replyMsg = reply.TextMsg(
                            wechatmp_msg.from_user_id, wechatmp_msg.to_user_id, content
                        )
                        return replyMsg.send()
                    channel.query1[cache_key] = False
                    channel.query2[cache_key] = False
                    channel.query3[cache_key] = False
                # User request again, and the answer is not ready
                elif (
                    cache_key in channel.running
                    and channel.query1.get(cache_key) == True
                    and channel.query2.get(cache_key) == True
                    and channel.query3.get(cache_key) == True
                ):
                    channel.query1[
                        cache_key
                    ] = False  # To improve waiting experience, this can be set to True.
                    channel.query2[
                        cache_key
                    ] = False  # To improve waiting experience, this can be set to True.
                    channel.query3[cache_key] = False
                # User request again, and the answer is ready
                elif cache_key in channel.cache_dict:
                    # Skip the waiting phase
                    channel.query1[cache_key] = True
                    channel.query2[cache_key] = True
                    channel.query3[cache_key] = True

                assert not (
                    cache_key in channel.cache_dict and cache_key in channel.running
                )

                if channel.query1.get(cache_key) == False:
                    # The first query from wechat official server
                    logger.debug("[wechatmp] query1 {}".format(cache_key))
                    channel.query1[cache_key] = True
                    cnt = 0
                    while cache_key in channel.running and cnt < 45:
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
                    while cache_key in channel.running and cnt < 45:
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
                    while cache_key in channel.running and cnt < 40:
                        cnt = cnt + 1
                        time.sleep(0.1)
                    if cnt == 40:
                        # Have waiting for 3x5 seconds
                        # return timeout message
                        reply_text = "【正在思考中，回复任意文字尝试获取回复】"
                        logger.info(
                            "[wechatmp] Three queries has finished For {}: {}".format(
                                from_user, message_id
                            )
                        )
                        replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                        return replyPost
                    else:
                        pass

                if (
                    cache_key not in channel.cache_dict
                    and cache_key not in channel.running
                ):
                    # no return because of bandwords or other reasons
                    return "success"

                # if float(time.time()) - float(query_time) > 4.8:
                #     reply_text = "【正在思考中，回复任意文字尝试获取回复】"
                #     logger.info("[wechatmp] Timeout for {} {}, return".format(from_user, message_id))
                #     replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                #     return replyPost

                if cache_key in channel.cache_dict:
                    content = channel.cache_dict[cache_key]
                    if len(content.encode("utf8")) <= MAX_UTF8_LEN:
                        reply_text = channel.cache_dict[cache_key]
                        channel.cache_dict.pop(cache_key)
                    else:
                        continue_text = "\n【未完待续，回复任意文字以继续】"
                        splits = split_string_by_utf8_length(
                            content,
                            MAX_UTF8_LEN - len(continue_text.encode("utf-8")),
                            max_split=1,
                        )
                        reply_text = splits[0] + continue_text
                        channel.cache_dict[cache_key] = splits[1]
                logger.info(
                    "[wechatmp] {}:{} Do send {}".format(
                        web.ctx.env.get("REMOTE_ADDR"),
                        web.ctx.env.get("REMOTE_PORT"),
                        reply_text,
                    )
                )
                replyPost = reply.TextMsg(from_user, to_user, reply_text).send()
                return replyPost

            elif wechatmp_msg.msg_type == "event":
                logger.info(
                    "[wechatmp] Event {} from {}".format(
                        wechatmp_msg.content, wechatmp_msg.from_user_id
                    )
                )
                content = subscribe_msg()
                replyMsg = reply.TextMsg(
                    wechatmp_msg.from_user_id, wechatmp_msg.to_user_id, content
                )
                return replyMsg.send()
            else:
                logger.info("暂且不处理")
                return "success"
        except Exception as exc:
            logger.exception(exc)
            return exc
