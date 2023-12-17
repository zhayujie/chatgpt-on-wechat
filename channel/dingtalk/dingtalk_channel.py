"""
钉钉通道接入

@author huiwen
@Date 2023/11/28
"""

# -*- coding=utf-8 -*-
import uuid

import requests
import web
from channel.dingtalk.dingtalk_message import DingTalkMessage
from bridge.context import Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.singleton import singleton
from config import conf
from common.expired_dict import ExpiredDict
from bridge.context import ContextType
from channel.chat_channel import ChatChannel, check_prefix
from common import utils
import json
import os



import argparse
import logging
from dingtalk_stream import AckMessage
import dingtalk_stream

@singleton
class DingTalkChanel(ChatChannel,dingtalk_stream.ChatbotHandler):
    dingtalk_client_id = conf().get('dingtalk_client_id')
    dingtalk_client_secret = conf().get('dingtalk_client_secret')
    
    def setup_logger(self):
        logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    def __init__(self):
        super().__init__()
        super(dingtalk_stream.ChatbotHandler, self).__init__()
        
        self.logger = self.setup_logger()
        # 历史消息id暂存，用于幂等控制
        self.receivedMsgs = ExpiredDict(60 * 60 * 7.1)
        
        logger.info("[dingtalk] client_id={}, client_secret={} ".format(
            self.dingtalk_client_id, self.dingtalk_client_secret))
        # 无需群校验和前缀
        conf()["group_name_white_list"] = ["ALL_GROUP"]
        
        

    def startup(self):
       
        credential = dingtalk_stream.Credential( self.dingtalk_client_id, self.dingtalk_client_secret)
        client = dingtalk_stream.DingTalkStreamClient(credential)
        client.register_callback_handler(dingtalk_stream.chatbot.ChatbotMessage.TOPIC,self)
        client.start_forever()

    def handle_single(self, cmsg:DingTalkMessage):
        # 处理单聊消息
        #  
    
        if cmsg.ctype == ContextType.VOICE:
           
            logger.debug("[dingtalk]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[dingtalk]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[dingtalk]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            expression = cmsg.my_msg
            
        cmsg.content = conf()["single_chat_prefix"][0] + cmsg.content
        
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        
        if context:
            self.produce(context)

    def handle_group(self, cmsg:DingTalkMessage):
        # 处理群聊消息
        #  
    
        if cmsg.ctype == ContextType.VOICE:
           
            logger.debug("[dingtalk]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[dingtalk]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[dingtalk]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            expression = cmsg.my_msg
            
        cmsg.content = conf()["group_chat_prefix"][0] + cmsg.content
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        context['no_need_at']=True
        if context:
            self.produce(context)


    async def process(self, callback: dingtalk_stream.CallbackMessage):
       


        try:
            
            incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
            dingtalk_msg = DingTalkMessage(incoming_message)
            if incoming_message.conversation_type == '1':
                self.handle_single(dingtalk_msg)
            else:
                self.handle_group(dingtalk_msg)   
            return AckMessage.STATUS_OK, 'OK'
        except Exception as e:
            logger.error(e)
            return self.FAILED_MSG


    def send(self, reply: Reply, context: Context):


        incoming_message = context.kwargs['msg'].incoming_message
        self.reply_text(reply.content, incoming_message)
       
        



    # def _compose_context(self, ctype: ContextType, content, **kwargs):
    #     context = Context(ctype, content)
    #     context.kwargs = kwargs
    #     if "origin_ctype" not in context:
    #         context["origin_ctype"] = ctype

    #     cmsg = context["msg"]
    #     context["session_id"] = cmsg.from_user_id
    #     context["receiver"] = cmsg.other_user_id

    #     if ctype == ContextType.TEXT:
    #         # 1.文本请求
    #         # 图片生成处理
    #         img_match_prefix = check_prefix(content, conf().get("image_create_prefix"))
    #         if img_match_prefix:
    #             content = content.replace(img_match_prefix, "", 1)
    #             context.type = ContextType.IMAGE_CREATE
    #         else:
    #             context.type = ContextType.TEXT
    #         context.content = content.strip()

    #     elif context.type == ContextType.VOICE:
    #         # 2.语音请求
    #         if "desire_rtype" not in context and conf().get("voice_reply_voice"):
    #             context["desire_rtype"] = ReplyType.VOICE

    #     return context
