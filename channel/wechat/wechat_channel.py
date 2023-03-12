# encoding:utf-8

"""
wechat channel
"""

import itchat
import json
from itchat.content import *
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from common.log import logger
from common.tmp_dir import TmpDir
from config import conf
from plugins import *

import requests
import io


thread_pool = ThreadPoolExecutor(max_workers=8)


@itchat.msg_register(TEXT)
def handler_single_msg(msg):
    WechatChannel().handle_text(msg)
    return None


@itchat.msg_register(TEXT, isGroupChat=True)
def handler_group_msg(msg):
    WechatChannel().handle_group(msg)
    return None


@itchat.msg_register(VOICE)
def handler_single_voice(msg):
    WechatChannel().handle_voice(msg)
    return None


class WechatChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        # login by scan QRCode
        itchat.auto_login(enableCmdQR=2)

        # start message listener
        itchat.run()

    # handle_* 系列函数处理收到的消息后构造context，然后调用handle函数处理context
    # context是一个字典，包含了消息的所有信息，包括以下key
    #   type: 消息类型，包括TEXT、VOICE、IMAGE_CREATE
    #   content: 消息内容，如果是TEXT类型，content就是文本内容，如果是VOICE类型，content就是语音文件名，如果是IMAGE_CREATE类型，content就是图片生成命令
    #   session_id: 会话id
    #   isgroup: 是否是群聊
    #   msg: 原始消息对象
    #   receiver: 需要回复的对象

    def handle_voice(self, msg):
        if conf().get('speech_recognition') != True:
            return
        logger.debug("[WX]receive voice msg: " + msg['FileName'])
        from_user_id = msg['FromUserName']
        other_user_id = msg['User']['UserName']
        if from_user_id == other_user_id:
            context = {'isgroup': False, 'msg': msg, 'receiver': other_user_id}
            context['type'] = 'VOICE'
            context['session_id'] = other_user_id
            thread_pool.submit(self.handle, context)

    def handle_text(self, msg):
        logger.debug("[WX]receive text msg: " + json.dumps(msg, ensure_ascii=False))
        content = msg['Text']
        from_user_id = msg['FromUserName']
        to_user_id = msg['ToUserName']              # 接收人id
        other_user_id = msg['User']['UserName']     # 对手方id
        match_prefix = check_prefix(content, conf().get('single_chat_prefix'))
        if "」\n- - - - - - - - - - - - - - -" in content:
            logger.debug("[WX]reference query skipped")
            return
        if match_prefix:
            content = content.replace(match_prefix, '', 1).strip()
        else:
            return
        context = {'isgroup': False, 'msg': msg, 'receiver': other_user_id}
        context['session_id'] = other_user_id

        img_match_prefix = check_prefix(content, conf().get('image_create_prefix'))
        if img_match_prefix:
            content = content.replace(img_match_prefix, '', 1).strip()
            context['type'] = 'IMAGE_CREATE'
        else:
            context['type'] = 'TEXT'

        context['content'] = content
        thread_pool.submit(self.handle, context)

    def handle_group(self, msg):
        logger.debug("[WX]receive group msg: " + json.dumps(msg, ensure_ascii=False))
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        if not group_name:
            return ""
        origin_content = msg['Content']
        content = msg['Content']
        content_list = content.split(' ', 1)
        context_special_list = content.split('\u2005', 1)
        if len(context_special_list) == 2:
            content = context_special_list[1]
        elif len(content_list) == 2:
            content = content_list[1]
        if "」\n- - - - - - - - - - - - - - -" in content:
            logger.debug("[WX]reference query skipped")
            return ""
        config = conf()
        match_prefix = (msg['IsAt'] and not config.get("group_at_off", False)) or check_prefix(origin_content, config.get('group_chat_prefix')) \
                       or check_contain(origin_content, config.get('group_chat_keyword'))
        if ('ALL_GROUP' in config.get('group_name_white_list') or group_name in config.get('group_name_white_list') or check_contain(group_name, config.get('group_name_keyword_white_list'))) and match_prefix:
            context = { 'isgroup': True, 'msg': msg, 'receiver': group_id}
            
            img_match_prefix = check_prefix(content, conf().get('image_create_prefix'))
            if img_match_prefix:
                content = content.replace(img_match_prefix, '', 1).strip()
                context['type'] = 'IMAGE_CREATE'
            else:
                context['type'] = 'TEXT'
            context['content'] = content

            group_chat_in_one_session = conf().get('group_chat_in_one_session', [])
            if ('ALL_GROUP' in group_chat_in_one_session or
                    group_name in group_chat_in_one_session or
                    check_contain(group_name, group_chat_in_one_session)):
                context['session_id'] = group_id
            else:
                context['session_id'] = msg['ActualUserName']

            thread_pool.submit(self.handle, context)

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply, receiver):
        if reply['type'] == 'TEXT':
            itchat.send(reply['content'], toUserName=receiver)
            logger.info('[WX] sendMsg={}, receiver={}'.format(reply, receiver))
        elif reply['type'] == 'ERROR' or reply['type'] == 'INFO':
            itchat.send(reply['content'], toUserName=receiver)
            logger.info('[WX] sendMsg={}, receiver={}'.format(reply, receiver))
        elif reply['type'] == 'VOICE':
            itchat.send_file(reply['content'], toUserName=receiver)
            logger.info('[WX] sendFile={}, receiver={}'.format(reply['content'], receiver))
        elif reply['type']=='IMAGE_URL': # 从网络下载图片
            img_url = reply['content']
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info('[WX] sendImage url=, receiver={}'.format(img_url,receiver))
        elif reply['type']=='IMAGE': # 从文件读取图片
            image_storage = reply['content']
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info('[WX] sendImage, receiver={}'.format(receiver))

    # 处理消息 TODO: 如果wechaty解耦，此处逻辑可以放置到父类
    def handle(self, context):
        reply = {}

        logger.debug('[WX] ready to handle context: {}'.format(context))
        
        # reply的构建步骤
        e_context = PluginManager().emit_event(EventContext(Event.ON_HANDLE_CONTEXT, {'channel' : self, 'context': context, 'reply': reply}))
        reply=e_context['reply']
        if not e_context.is_pass():
            logger.debug('[WX] ready to handle context: type={}, content={}'.format(context['type'], context['content']))
            if context['type'] == 'TEXT' or context['type'] == 'IMAGE_CREATE':
                reply = super().build_reply_content(context['content'], context)
            elif context['type'] == 'VOICE':
                msg = context['msg']
                file_name = TmpDir().path() + msg['FileName']
                msg.download(file_name)
                reply = super().build_voice_to_text(file_name)
                if reply['type'] != 'ERROR' and reply['type'] != 'INFO':
                    reply = super().build_reply_content(reply['content'], context)
                    if reply['type'] == 'TEXT':
                        if conf().get('voice_reply_voice'):
                            reply = super().build_text_to_voice(reply['content'])
            else:
                logger.error('[WX] unknown context type: {}'.format(context['type']))
                return

        logger.debug('[WX] ready to decorate reply: {}'.format(reply))
        
        # reply的包装步骤
        if reply and reply['type']:
            e_context = PluginManager().emit_event(EventContext(Event.ON_DECORATE_REPLY, {'channel' : self, 'context': context, 'reply': reply}))
            reply=e_context['reply']
            if not e_context.is_pass() and reply and reply['type']:
                if reply['type'] == 'TEXT':
                    reply_text = reply['content']
                    if context['isgroup']:
                        reply_text = '@' +  context['msg']['ActualNickName'] + ' ' + reply_text.strip()
                        reply_text = conf().get("group_chat_reply_prefix", "")+reply_text
                    else:
                        reply_text = conf().get("single_chat_reply_prefix", "")+reply_text
                    reply['content'] = reply_text
                elif reply['type'] == 'ERROR' or reply['type'] == 'INFO':
                    reply['content'] = reply['type']+": " + reply['content']
                elif reply['type'] == 'IMAGE_URL' or reply['type'] == 'VOICE' or reply['type'] == 'IMAGE':
                    pass
                else:
                    logger.error('[WX] unknown reply type: {}'.format(reply['type']))
                    return

        # reply的发送步骤   
        if reply and reply['type']:
            e_context = PluginManager().emit_event(EventContext(Event.ON_SEND_REPLY, {'channel' : self, 'context': context, 'reply': reply}))
            reply=e_context['reply']
            if not e_context.is_pass() and reply and reply['type']:
                logger.debug('[WX] ready to send reply: {} to {}'.format(reply, context['receiver']))
                self.send(reply, context['receiver'])


def check_prefix(content, prefix_list):
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return None


def check_contain(content, keyword_list):
    if not keyword_list:
        return None
    for ky in keyword_list:
        if content.find(ky) != -1:
            return True
    return None
