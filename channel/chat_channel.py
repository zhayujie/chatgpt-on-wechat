


import os
import re
import time
from common.expired_dict import ExpiredDict
from channel.channel import Channel
from bridge.reply import *
from bridge.context import *
from config import conf
from common.log import logger
from plugins import *
try:
    from voice.audio_convert import any_to_wav
except Exception as e:
    pass

# 抽象类, 它包含了与消息通道无关的通用处理逻辑
class ChatChannel(Channel):
    name = None # 登录的用户名
    user_id = None # 登录的用户id
    def __init__(self):
        pass

    # 根据消息构造context，消息内容相关的触发项写在这里
    def _compose_context(self, ctype: ContextType, content, **kwargs):
        context = Context(ctype, content)
        context.kwargs = kwargs
        # context首次传入时，origin_ctype是None, 
        # 引入的起因是：当输入语音时，会嵌套生成两个context，第一步语音转文本，第二步通过文本生成文字回复。
        # origin_ctype用于第二步文本回复时，判断是否需要匹配前缀，如果是私聊的语音，就不需要匹配前缀
        if 'origin_ctype' not in context:  
            context['origin_ctype'] = ctype
        # context首次传入时，receiver是None，根据类型设置receiver
        first_in = 'receiver' not in context
        # 群名匹配过程，设置session_id和receiver
        if first_in: # context首次传入时，receiver是None，根据类型设置receiver
            config = conf()
            cmsg = context['msg']
            if cmsg.from_user_id == self.user_id:
                logger.debug("[WX]self message skipped")
                return None
            if context["isgroup"]:
                group_name = cmsg.other_user_nickname
                group_id = cmsg.other_user_id

                group_name_white_list = config.get('group_name_white_list', [])
                group_name_keyword_white_list = config.get('group_name_keyword_white_list', [])
                if any([group_name in group_name_white_list, 'ALL_GROUP' in group_name_white_list, check_contain(group_name, group_name_keyword_white_list)]):
                    group_chat_in_one_session = conf().get('group_chat_in_one_session', [])
                    session_id = cmsg.actual_user_id
                    if any([group_name in group_chat_in_one_session, 'ALL_GROUP' in group_chat_in_one_session]):
                        session_id = group_id
                else:
                    return None
                context['session_id'] = session_id
                context['receiver'] = group_id
            else:
                context['session_id'] = cmsg.other_user_id
                context['receiver'] = cmsg.other_user_id

        # 消息内容匹配过程，并处理content
        if ctype == ContextType.TEXT:
            if first_in and "」\n- - - - - - -" in content: # 初次匹配 过滤引用消息
                logger.debug("[WX]reference query skipped")
                return None
            
            if context["isgroup"]: # 群聊
                # 校验关键字
                match_prefix = check_prefix(content, conf().get('group_chat_prefix'))
                match_contain = check_contain(content, conf().get('group_chat_keyword'))
                if match_prefix is not None or match_contain is not None:
                    if match_prefix:
                        content = content.replace(match_prefix, '', 1).strip()
                elif context['msg'].is_at and not conf().get("group_at_off", False):
                    logger.info("[WX]receive group at, continue")
                    pattern = f'@{self.name}(\u2005|\u0020)'
                    content = re.sub(pattern, r'', content)
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
            if 'desire_rtype' not in context and conf().get('always_reply_voice'):
                context['desire_rtype'] = ReplyType.VOICE
        elif context.type == ContextType.VOICE: 
            if 'desire_rtype' not in context and conf().get('voice_reply_voice'):
                context['desire_rtype'] = ReplyType.VOICE

        return context

    # 处理消息 TODO: 如果wechaty解耦，此处逻辑可以放置到父类
    def _handle(self, context: Context):
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
                cmsg = context['msg']
                cmsg.prepare()
                file_path = context.content
                wav_path = os.path.splitext(file_path)[0] + '.wav'
                try:
                    any_to_wav(file_path, wav_path) 
                except Exception as e:  # 转换失败，直接使用mp3，对于某些api，mp3也可以识别
                    logger.warning("[WX]any to wav error, use raw path. " + str(e))
                    wav_path = file_path
                # 语音识别
                reply = super().build_voice_to_text(wav_path)
                # 删除临时文件
                try:
                    os.remove(file_path)
                    if wav_path != file_path:
                        os.remove(wav_path)
                except Exception as e:
                    pass
                    # logger.warning("[WX]delete temp file error: " + str(e))

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
                        reply_text = '@' +  context['msg'].actual_user_nickname + ' ' + reply_text.strip()
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
                logger.debug('[WX] ready to send reply: {}, context: {}'.format(reply, context))
                self._send(reply, context)

    def _send(self, reply: Reply, context: Context, retry_cnt = 0):
        try:
            self.send(reply, context)
        except Exception as e:
            logger.error('[WX] sendMsg error: {}'.format(str(e)))
            if isinstance(e, NotImplementedError):
                return
            logger.exception(e)
            if retry_cnt < 2:
                time.sleep(3+3*retry_cnt)
                self._send(reply, context, retry_cnt+1)

    

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
