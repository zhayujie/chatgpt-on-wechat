# encoding:utf-8

"""
wechat channel
"""

import os
import re
import requests
import io
import time
from common.singleton import singleton
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
from common.expired_dict import ExpiredDict
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

def _check(func):
    def wrapper(self, msg):
        msgId = msg['MsgId']
        if msgId in self.receivedMsgs:
            logger.info("Wechat message {} already received, ignore".format(msgId))
            return
        self.receivedMsgs[msgId] = msg
        create_time = msg['CreateTime']             # 消息时间
        if conf().get('hot_reload') == True and int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[WX]history message {} skipped".format(msgId))
            return
        return func(self, msg)
    return wrapper

@singleton
class WechatChannel(Channel):
    def __init__(self):
        self.user_id = None
        self.name = None
        self.receivedMsgs = ExpiredDict(60*60*24) 

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
        self.user_id = itchat.instance.storageClass.userName
        self.name = itchat.instance.storageClass.nickName
        logger.info("Wechat login success, user_id: {}, nickname: {}".format(self.user_id, self.name))
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
    #        origin_ctype: 原始消息类型，语音转文字后，私聊时如果匹配前缀失败，会根据初始消息是否是语音来放宽触发规则
    #        desire_rtype: 希望回复类型，默认是文本回复，设置为ReplyType.VOICE是语音回复

    @time_checker
    @_check
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
            context = self._compose_context(ContextType.VOICE, msg['FileName'], isgroup=False, msg=msg, receiver=other_user_id, session_id=other_user_id)
            if context:
                thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)

    @time_checker
    @_check
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
        if "」\n- - - - - - - - - - - - - - -" in content:
            logger.debug("[WX]reference query skipped")
            return
        
        context = self._compose_context(ContextType.TEXT, content, isgroup=False, msg=msg, receiver=other_user_id, session_id=other_user_id)
        if context:
            thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)

    @time_checker
    @_check
    def handle_group(self, msg):
        logger.debug("[WX]receive group msg: " + json.dumps(msg, ensure_ascii=False))
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        if not group_name:
            return ""
        content = msg.content
        if "」\n- - - - - - - - - - - - - - -" in content:
            logger.debug("[WX]reference query skipped")
            return ""
        pattern = f'@{self.name}(\u2005|\u0020)'
        content = re.sub(pattern, r'', content)

        config = conf()
        group_name_white_list = config.get('group_name_white_list', [])
        group_name_keyword_white_list = config.get('group_name_keyword_white_list', [])

        if any([group_name in group_name_white_list, 'ALL_GROUP' in group_name_white_list, check_contain(group_name, group_name_keyword_white_list)]):
            group_chat_in_one_session = conf().get('group_chat_in_one_session', [])
            session_id = msg['ActualUserName']
            if any([group_name in group_chat_in_one_session, 'ALL_GROUP' in group_chat_in_one_session]):
                session_id = group_id
            context = self._compose_context(ContextType.TEXT, content, isgroup=True, msg=msg, receiver=group_id, session_id=session_id)
            if context:
                thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)
    
    @time_checker
    @_check
    def handle_group_voice(self, msg):
        if conf().get('group_speech_recognition', False) != True:
            return
        logger.debug("[WX]receive voice for group msg: " + msg['FileName'])
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        # 验证群名
        if not group_name:
            return ""
        
        config = conf()
        group_name_white_list = config.get('group_name_white_list', [])
        group_name_keyword_white_list = config.get('group_name_keyword_white_list', [])
        if any([group_name in group_name_white_list, 'ALL_GROUP' in group_name_white_list, check_contain(group_name, group_name_keyword_white_list)]):
            group_chat_in_one_session = conf().get('group_chat_in_one_session', [])
            session_id =msg['ActualUserName']
            if any([group_name in group_chat_in_one_session, 'ALL_GROUP' in group_chat_in_one_session]):
                session_id = group_id
            context = self._compose_context(ContextType.VOICE, msg['FileName'], isgroup=True, msg=msg, receiver=group_id, session_id=session_id)
            if context:
                thread_pool.submit(self.handle, context).add_done_callback(thread_pool_callback)

    # 根据消息构造context，消息内容相关的触发项写在这里
    def _compose_context(self, ctype: ContextType, content, **kwargs):
        context = Context(ctype, content)
        context.kwargs = kwargs
        if 'origin_ctype' not in context:
            context['origin_ctype'] = ctype

        if ctype == ContextType.TEXT:
            if context["isgroup"]: # 群聊
                # 校验关键字
                match_prefix = check_prefix(content, conf().get('group_chat_prefix'))
                match_contain = check_contain(content, conf().get('group_chat_keyword'))
                if match_prefix is not None or match_contain is not None:
                    # 判断如果匹配到自定义前缀，则返回过滤掉前缀+空格后的内容，用于实现类似自定义+前缀触发生成AI图片的功能
                    if match_prefix:
                        content = content.replace(match_prefix, '', 1).strip()
                elif context['msg']['IsAt'] and not conf().get("group_at_off", False):
                    logger.info("[WX]receive group at, continue")
                elif context["origin_ctype"] == ContextType.VOICE:
                    logger.info("[WX]receive group voice, checkprefix didn't match")
                    return None
                else:
                    return None
            else: # 单聊
                match_prefix = check_prefix(content, conf().get('single_chat_prefix'))  
                if match_prefix is not None: # 判断如果匹配到自定义前缀，则返回过滤掉前缀+空格后的内容
                    content = content.replace(match_prefix, '', 1).strip()
                elif context["origin_ctype"] == ContextType.VOICE: # 如果源消息是私聊的语音消息，允许不匹配前缀，放宽条件
                    pass
                else:
                    return None                                       
            img_match_prefix = check_prefix(content, conf().get('image_create_prefix'))
            if img_match_prefix:
                content = content.replace(img_match_prefix, '', 1).strip()
                context.type = ContextType.IMAGE_CREATE
            else:
                context.type = ContextType.TEXT
            context.content = content
        elif context.type == ContextType.VOICE:
            if 'desire_rtype' not in context and conf().get('voice_reply_voice'):
                context['desire_rtype'] = ReplyType.VOICE
        return context
    
    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, receiver, retry_cnt = 0):
        try:
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
        except Exception as e:
            logger.error('[WX] sendMsg error: {}, receiver={}'.format(e, receiver))
            if retry_cnt < 2:
                time.sleep(3+3*retry_cnt)
                self.send(reply, receiver, retry_cnt + 1)

    # 处理消息 TODO: 如果wechaty解耦，此处逻辑可以放置到父类
    def handle(self, context: Context):
        if context is None or not context.content:
            return
        logger.debug('[WX] ready to handle context: {}'.format(context))
        # reply的构建步骤
        reply = self._generate_reply(context)

        logger.debug('[WX] ready to decorate reply: {}'.format(reply))
        # reply的包装步骤
        reply = self._decorate_reply(context, reply)

        # reply的发送步骤
        self._send_reply(context, reply)

    def _generate_reply(self, context: Context, reply: Reply = Reply()) -> Reply:
        e_context = PluginManager().emit_event(EventContext(Event.ON_HANDLE_CONTEXT, {
            'channel': self, 'context': context, 'reply': reply}))
        reply = e_context['reply']
        if not e_context.is_pass():
            logger.debug('[WX] ready to handle context: type={}, content={}'.format(context.type, context.content))
            if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE:  # 文字和图片消息
                reply = super().build_reply_content(context.content, context)
            elif context.type == ContextType.VOICE:  # 语音消息
                msg = context['msg']
                mp3_path = TmpDir().path() + context.content
                msg.download(mp3_path)
                # mp3转wav
                wav_path = os.path.splitext(mp3_path)[0] + '.wav'
                try:
                    mp3_to_wav(mp3_path=mp3_path, wav_path=wav_path)
                except Exception as e:  # 转换失败，直接使用mp3，对于某些api，mp3也可以识别
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

                if reply.type == ReplyType.TEXT:
                    new_context = self._compose_context(
                        ContextType.TEXT, reply.content, **context.kwargs)
                    if new_context:
                        reply = self._generate_reply(new_context)
                    else:
                        return
            else:
                logger.error('[WX] unknown context type: {}'.format(context.type))
                return
        return reply

    def _decorate_reply(self, context: Context, reply: Reply) -> Reply:
        if reply and reply.type:
            e_context = PluginManager().emit_event(EventContext(Event.ON_DECORATE_REPLY, {
                'channel': self, 'context': context, 'reply': reply}))
            reply = e_context['reply']
            desire_rtype = context.get('desire_rtype')
            if not e_context.is_pass() and reply and reply.type:
                if reply.type == ReplyType.TEXT:
                    reply_text = reply.content
                    if desire_rtype == ReplyType.VOICE:
                        reply = super().build_text_to_voice(reply.content)
                        return self._decorate_reply(context, reply)
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
            if desire_rtype and desire_rtype != reply.type and reply.type not in [ReplyType.ERROR, ReplyType.INFO]:
                logger.warning('[WX] desire_rtype: {}, but reply type: {}'.format(context.get('desire_rtype'), reply.type))
            return reply

    def _send_reply(self, context: Context, reply: Reply):
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
