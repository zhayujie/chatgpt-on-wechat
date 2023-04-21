import time

import web

from channel.wechatmp.wechatmp_message import WeChatMPMessage
from bridge.context import *
from bridge.reply import *
from channel.wechatmp.common import *
from channel.wechatmp.wechatmp_channel import WechatMPChannel
from wechatpy import parse_message
from common.log import logger
from config import conf
from wechatpy.replies import create_reply

# This class is instantiated once per query
class Query:
    def GET(self):
        return verify_server(web.input())

    def POST(self):
        # Make sure to return the instance that first created, @singleton will do that.
        channel = WechatMPChannel()
        try:
            verify_server(web.input())
            message = web.data() # todo crypto
            # logger.debug("[wechatmp] Receive request:\n" + webData.decode("utf-8"))
            msg = parse_message(message)
            if msg.type == "event":
                logger.info(
                    "[wechatmp] Event {} from {}".format(
                        msg.event, msg.source
                    )
                )
                if msg.event in ["subscribe", "subscribe_scan"]:
                    reply_text = subscribe_msg()
                    replyPost = create_reply(reply_text, msg)
                    return replyPost.render()
                else:
                    return "success"
            wechatmp_msg = WeChatMPMessage(msg, client=channel.client)
            if wechatmp_msg.ctype in [ContextType.TEXT, ContextType.IMAGE, ContextType.VOICE]:
                from_user = wechatmp_msg.from_user_id
                content = wechatmp_msg.content
                message_id = wechatmp_msg.msg_id

                logger.info(
                    "[wechatmp] {}:{} Receive post query {} {}: {}".format(
                        web.ctx.env.get("REMOTE_ADDR"),
                        web.ctx.env.get("REMOTE_PORT"),
                        from_user,
                        message_id,
                        content,
                    )
                )
                if msg.type == "voice" and wechatmp_msg.ctype == ContextType.TEXT and conf().get("voice_reply_voice", False):
                    context = channel._compose_context(
                        wechatmp_msg.ctype, content, isgroup=False, desire_rtype=ReplyType.VOICE, msg=wechatmp_msg
                    )
                else:
                    context = channel._compose_context(
                        wechatmp_msg.ctype, content, isgroup=False, msg=wechatmp_msg
                    )
                if context:
                    # set private openai_api_key
                    # if from_user is not changed in itchat, this can be placed at chat_channel
                    user_data = conf().get_user_data(from_user)
                    context["openai_api_key"] = user_data.get(
                        "openai_api_key"
                    )  # None or user openai_api_key
                    channel.produce(context)
                # The reply will be sent by channel.send() in another thread
                return "success"
            else:
                logger.info("暂且不处理")
                return "success"
        except Exception as exc:
            logger.exception(exc)
            return exc
