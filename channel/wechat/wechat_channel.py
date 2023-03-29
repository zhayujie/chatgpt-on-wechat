# encoding:utf-8

"""
wechat channel
"""

import os
import requests
import io
import time
from lib import itchat
import json
from lib.itchat.content import *
from bridge.reply import *
from bridge.context import *
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from common.log import logger
from common.tmp_dir import TmpDir
from config import conf
from common.time_check import time_checker
from plugins import *
try:
    from voice.audio_convert import mp3_to_wav
except Exception as e:
    pass
thread_pool = ThreadPoolExecutor(max_workers=8)


def thread_pool_callback(worker):
    worker_exception = worker.exception()
    if worker_exception:
        logger.exception("Worker return exception: {}".format(worker_exception))


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
    
@itchat.msg_register(VOICE, isGroupChat=True)
def handler_group_voice(msg):
    WechatChannel().handle_group_voice(msg)
    return None



class WechatChannel(Channel):
    def __init__(self):
        self.userName = None
        self.nickName = None

    def startup(self):

        itchat.instance.receivingRetryCount = 600  # 修改断线超时时间
        # login by scan QRCode
        hotReload = conf().get('hot_reload', False)
        try:
            itchat.auto_login(enableCmdQR=2, hotReload=hotReload)
        except Exception as e:
            if hotReload:
                logger.error("Hot reload failed, try to login without hot reload")
                itchat.logout()
                os.remove("itchat.pkl")
                itchat.auto_login(enableCmdQR=2, hotReload=hotReload)
            else:
                raise e
        self.userName = itchat.instance.storageClass.userName
        self.nickName = itchat.instance.storageClass.nickName
        logger.info("Wechat login success, username: {}, nickname: {}".format(self.userName, self.nickName))
        # start message listener
        itchat.run()

    # handle_* 系列函数处理收到的消息后构造Context，然后传入handle函数中处理Context和发送回复
    # Context包含了消息的所有信息，包括以下属性
    #   type 消息类型, 包括TEXT、VOICE、IMAGE_CREATE
    #   content 消息内容，如果是TEXT类型，content就是文本内容，如果是VOICE类型，content就是语音文件名，如果是IMAGE_CREATE类型，content就是图片生成命令
    #   kwargs 附加参数字典，包含以下的key：
    #        session_id: 会话id
    #        isgroup: 是否是群聊
    #        receiver: 需要回复的对象
    #        msg: itchat的原始消息对象

    def handle_voice(self, msg):
        if conf().get('speech_recognition') != True:
            return
        logger.debug("[WX]receive voice msg: " + msg['FileName'])
        to_user_id = msg['ToUserName']
        from_user_id = msg['FromUserName']
        try:
            other_user_id = msg['User']['UserName']     # 对手方id
        except Exception as e:
            logger.warn("[WX]get other_user_id failed: " + str(e))
            if from_user_id == self.userName:
                other_user_id = to_user_id
            else:
                other_user_id = from_user_id
        if from_user_id == other_user_id:
            context = Context(ContextType.VOICE,msg['FileName'])
            context.kwargs = {'isgroup': False, 'msg': msg, 'receiver': other_user_id, 'session_id': other_user_id}
            thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)

    @time_checker
    def handle_text(self, msg):
        logger.debug("[WX]receive text msg: " + json.dumps(msg, ensure_ascii=False))
        content = msg['Text']
        from_user_id = msg['FromUserName']
        to_user_id = msg['ToUserName']              # 接收人id
        try:
            other_user_id = msg['User']['UserName']     # 对手方id
        except Exception as e:
            logger.warn("[WX]get other_user_id failed: " + str(e))
            if from_user_id == self.userName:
                other_user_id = to_user_id
            else:
                other_user_id = from_user_id
        create_time = msg['CreateTime']             # 消息时间
        match_prefix = check_prefix(content, conf().get('single_chat_prefix'))
        if conf().get('hot_reload') == True and int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[WX]history message skipped")
            return
        if "」\n- - - - - - - - - - - - - - -" in content:
            logger.debug("[WX]reference query skipped")
            return
        if match_prefix:
            content = content.replace(match_prefix, '', 1).strip()
        elif match_prefix is None:
            return
        context = Context()
        context.kwargs = {'isgroup': False, 'msg': msg,
                          'receiver': other_user_id, 'session_id': other_user_id}

        img_match_prefix = check_prefix(content, conf().get('image_create_prefix'))
        if img_match_prefix:
            content = content.replace(img_match_prefix, '', 1).strip()
            context.type = ContextType.IMAGE_CREATE
        else:
            context.type = ContextType.TEXT

        context.content = content
        thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)

    @time_checker
    def handle_group(self, msg):
        logger.debug("[WX]receive group msg: " + json.dumps(msg, ensure_ascii=False))
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        create_time = msg['CreateTime']             # 消息时间
        if conf().get('hot_reload') == True and int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[WX]history group message skipped")
            return
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
            context = Context()
            context.kwargs = { 'isgroup': True, 'msg': msg, 'receiver': group_id}

            img_match_prefix = check_prefix(content, conf().get('image_create_prefix'))
            if img_match_prefix:
                content = content.replace(img_match_prefix, '', 1).strip()
                context.type = ContextType.IMAGE_CREATE
            else:
                context.type = ContextType.TEXT
            context.content = content

            group_chat_in_one_session = conf().get('group_chat_in_one_session', [])
            if ('ALL_GROUP' in group_chat_in_one_session or
                    group_name in group_chat_in_one_session or
                    check_contain(group_name, group_chat_in_one_session)):
                context['session_id'] = group_id
            else:
                context['session_id'] = msg['ActualUserName']

            thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)

    def handle_group_voice(self, msg):
        if conf().get('group_speech_recognition', False) != True:
            return
        logger.debug("[WX]receive voice for group msg: " + msg['FileName'])
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        create_time = msg['CreateTime']             # 消息时间
        if conf().get('hot_reload') == True and int(create_time) < int(time.time()) - 60:    #跳过1分钟前的历史消息
            logger.debug("[WX]history group voice skipped")
            return
        # 验证群名
        if not group_name:
            return ""
        if ('ALL_GROUP' in conf().get('group_name_white_list') or group_name in conf().get('group_name_white_list') or check_contain(group_name, conf().get('group_name_keyword_white_list'))):
            context = Context(ContextType.VOICE,msg['FileName'])
            context.kwargs = {'isgroup': True, 'msg': msg, 'receiver': group_id}

            group_chat_in_one_session = conf().get('group_chat_in_one_session', [])
            if ('ALL_GROUP' in group_chat_in_one_session or
                    group_name in group_chat_in_one_session or
                    check_contain(group_name, group_chat_in_one_session)):
                context['session_id'] = group_id
            else:
                context['session_id'] = msg['ActualUserName']

            thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, receiver):
        if reply.type == ReplyType.TEXT:
            itchat.send(reply.content, toUserName=receiver)
            logger.info('[WX] sendMsg={}, receiver={}'.format(reply, receiver))
        elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
            itchat.send(reply.content, toUserName=receiver)
            logger.info('[WX] sendMsg={}, receiver={}'.format(reply, receiver))
        elif reply.type == ReplyType.VOICE:
            itchat.send_file(reply.content, toUserName=receiver)
            logger.info('[WX] sendFile={}, receiver={}'.format(reply.content, receiver))
        elif reply.type == ReplyType.IMAGE_URL: # 从网络下载图片
            img_url = reply.content
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info('[WX] sendImage url={}, receiver={}'.format(img_url,receiver))
        elif reply.type == ReplyType.IMAGE: # 从文件读取图片
            image_storage = reply.content
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info('[WX] sendImage, receiver={}'.format(receiver))

    # 处理消息 TODO: 如果wechaty解耦，此处逻辑可以放置到父类
    def handle(self, context):
        if not context.content:
            return 
        
        reply = Reply()

        logger.debug('[WX] ready to handle context: {}'.format(context))

        # reply的构建步骤
        e_context = PluginManager().emit_event(EventContext(Event.ON_HANDLE_CONTEXT, {
            'channel': self, 'context': context, 'reply': reply}))
        reply = e_context['reply']
        if not e_context.is_pass():
            logger.debug('[WX] ready to handle context: type={}, content={}'.format(context.type, context.content))
            if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE: # 文字和图片消息
                reply = super().build_reply_content(context.content, context)
            elif context.type == ContextType.VOICE: # 语音消息
                msg = context['msg']
                mp3_path = TmpDir().path() + context.content
                msg.download(mp3_path)
                # mp3转wav
                wav_path = os.path.splitext(mp3_path)[0] + '.wav'
                try:
                    mp3_to_wav(mp3_path=mp3_path, wav_path=wav_path)
                except Exception as e: # 转换失败，直接使用mp3，对于某些api，mp3也可以识别
                    logger.warning("[WX]mp3 to wav error, use mp3 path. " + str(e))
                    wav_path = mp3_path
                # 语音识别
                reply = super().build_voice_to_text(wav_path)
                # 删除临时文件
                try:
                    os.remove(wav_path)
                    os.remove(mp3_path)
                except Exception as e:
                    logger.warning("[WX]delete temp file error: " + str(e))

                if reply.type != ReplyType.ERROR and reply.type != ReplyType.INFO:
                    content = reply.content  # 语音转文字后，将文字内容作为新的context
                    context.type = ContextType.TEXT
                    if context["isgroup"]: # 群聊
                        # 校验关键字
                        match_prefix = check_prefix(content, conf().get('group_chat_prefix'))
                        match_contain = check_contain(content, conf().get('group_chat_keyword'))
                        if match_prefix is not None or match_contain is not None:
                            # 判断如果匹配到自定义前缀，则返回过滤掉前缀+空格后的内容，用于实现类似自定义+前缀触发生成AI图片的功能
                            if match_prefix:
                                content = content.replace(match_prefix, '', 1).strip()
                        else:
                            logger.info("[WX]receive voice, checkprefix didn't match")
                            return
                    else: # 单聊
                        match_prefix = check_prefix(content, conf().get('single_chat_prefix'))  
                        if match_prefix: # 判断如果匹配到自定义前缀，则返回过滤掉前缀+空格后的内容
                            content = content.replace(match_prefix, '', 1).strip()
                                               
                    img_match_prefix = check_prefix(content, conf().get('image_create_prefix'))
                    if img_match_prefix:
                        content = content.replace(img_match_prefix, '', 1).strip()
                        context.type = ContextType.IMAGE_CREATE
                    else:
                        context.type = ContextType.TEXT
                    context.content = content
                    reply = super().build_reply_content(context.content, context)
                    if reply.type == ReplyType.TEXT:
                        if conf().get('voice_reply_voice'):
                            reply = super().build_text_to_voice(reply.content)
            else:
                logger.error('[WX] unknown context type: {}'.format(context.type))
                return

        logger.debug('[WX] ready to decorate reply: {}'.format(reply))

        # reply的包装步骤
        if reply and reply.type:
            e_context = PluginManager().emit_event(EventContext(Event.ON_DECORATE_REPLY, {
                'channel': self, 'context': context, 'reply': reply}))
            reply = e_context['reply']
            if not e_context.is_pass() and reply and reply.type:
                if reply.type == ReplyType.TEXT:
                    reply_text = reply.content
                    if context['isgroup']:
                        reply_text = '@' +  context['msg']['ActualNickName'] + ' ' + reply_text.strip()
                        reply_text = conf().get("group_chat_reply_prefix", "")+reply_text
                    else:
                        reply_text = conf().get("single_chat_reply_prefix", "")+reply_text
                    reply.content = reply_text
                elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
                    reply.content = str(reply.type)+":\n" + reply.content
                elif reply.type == ReplyType.IMAGE_URL or reply.type == ReplyType.VOICE or reply.type == ReplyType.IMAGE:
                    pass
                else:
                    logger.error('[WX] unknown reply type: {}'.format(reply.type))
                    return

        # reply的发送步骤
        if reply and reply.type:
            e_context = PluginManager().emit_event(EventContext(Event.ON_SEND_REPLY, {
                'channel': self, 'context': context, 'reply': reply}))
            reply = e_context['reply']
            if not e_context.is_pass() and reply and reply.type:
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
