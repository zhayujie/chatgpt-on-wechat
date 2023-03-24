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
from config import load_config, save_config, load_modes, save_modes
import requests
import io
import time

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


def check_super_user_command(content, config, msg):
    """
    检查是否是超级用户的命令
    超级用户可以用过#setting命令修改配置, 例如:
    1. 把chatgpt_test_100增加群白名单
        #setting:group_name_white_list=chatgpt_test_100
    2. 增加或修改emoji模式, character_desc为模式描述, pre_text为用户消息前缀, 用于强调提醒chatgpt保持设定
        #setting:mode=emoji=character_desc=从现在开始，你的回答必须把所有字替换成emoji，并保持原来的含义。你不能使用任何汉字或者英文。如有不适当的词语，将他们替换成对应的emoji=pre_text=只能用emoji回复
    改变完设置后会立即把配置保存到文件中, 由于load config改成每次都从文件中读取, 所以不需要重启服务
    :param content: 消息内容
    :param config: 配置
    :param msg: 消息
    """
    change_setting = False
    if content.startswith('#setting') and msg['ActualNickName'] in config['super_users']:
        change_setting = True
        setting = content.split(':')[1]
        params = setting.split('=')
        print(params)
        key = params[0].strip()
        if key == 'group_name_white_list':
            print('增加群白名单')
            val = params[1].strip()
            config[key].append(val)
            save_config(config)
        elif key == 'mode':
            mode = params[1]
            i = 2
            keys = ['character_desc', 'pre_text']
            modes = load_modes()
            mode_content = dict()
            if mode in modes:
                mode_content = modes[mode]

            while i < len(params):
                m_key = params[i].strip()
                val = params[i + 1].strip()
                print(m_key, val)
                if m_key in keys:
                    mode_content[m_key] = val
                i += 2
            modes[mode] = mode_content
            save_modes(modes)
    return change_setting


class WechatChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        # login by scan QRCode
        itchat.auto_login(enableCmdQR=2, hotReload=load_config().get('hot_reload', False))

        # start message listener
        itchat.run()

    def handle_voice(self, msg):
        if not load_config().get('speech_recognition'):
            return
        logger.debug("[WX]receive voice msg: " + msg['FileName'])
        thread_pool.submit(self._do_handle_voice, msg)

    def _do_handle_voice(self, msg):
        from_user_id = msg['FromUserName']
        other_user_id = msg['User']['UserName']
        if from_user_id == other_user_id:
            file_name = TmpDir().path() + msg['FileName']
            msg.download(file_name)
            query = super().build_voice_to_text(file_name)
            if load_config().get('voice_reply_voice'):
                self._do_send_voice(query, from_user_id)
            else:
                self._do_send_text(query, from_user_id)

    def handle_text(self, msg):
        logger.debug("[WX]receive text msg: " + json.dumps(msg, ensure_ascii=False))
        content = msg['Text']
        self._handle_single_msg(msg, content)

    def _handle_single_msg(self, msg, content):
        from_user_id = msg['FromUserName']
        to_user_id = msg['ToUserName']              # 接收人id
        other_user_id = msg['User']['UserName']     # 对手方id
        create_time = msg['CreateTime']             # 消息时间
        match_prefix = self.check_prefix(content, load_config().get('single_chat_prefix'))
        if load_config().get('hot_reload') and int(create_time) < int(time.time()) - 60:    #跳过1分钟前的历史消息
            logger.debug("[WX]history message skipped")
            return
        if "」\n- - - - - - - - - - - - - - -" in content:
            logger.debug("[WX]reference query skipped")
            return
        if from_user_id == other_user_id and match_prefix is not None:
            # 好友向自己发送消息
            if match_prefix != '':
                str_list = content.split(match_prefix, 1)
                if len(str_list) == 2:
                    content = str_list[1].strip()

            img_match_prefix = self.check_prefix(content, load_config().get('image_create_prefix'))
            if img_match_prefix:
                content = content.split(img_match_prefix, 1)[1].strip()
                thread_pool.submit(self._do_send_img, content, from_user_id)
            else:
                thread_pool.submit(self._do_send_text, content, from_user_id)
        elif to_user_id == other_user_id and match_prefix:
            # 自己给好友发送消息
            str_list = content.split(match_prefix, 1)
            if len(str_list) == 2:
                content = str_list[1].strip()
            img_match_prefix = self.check_prefix(content, load_config().get('image_create_prefix'))
            if img_match_prefix:
                content = content.split(img_match_prefix, 1)[1].strip()
                thread_pool.submit(self._do_send_img, content, to_user_id)
            else:
                thread_pool.submit(self._do_send_text, content, to_user_id)

    def handle_group(self, msg):
        logger.debug("[WX]receive group msg: " + json.dumps(msg, ensure_ascii=False))
        group_name = msg['User'].get('NickName', None)
        group_id = msg['User'].get('UserName', None)
        create_time = msg['CreateTime']             # 消息时间
        # 跳过1分钟前的历史消息
        if load_config().get('hot_reload') and int(create_time) < int(time.time()) - 60:
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

        config = load_config()
        # 检查是否为超级用户发送的命令
        change_setting = check_super_user_command(content, config, msg)
        if change_setting:
            config = load_config()

        match_prefix = (msg['IsAt'] and not config.get("group_at_off", False)) or self.check_prefix(origin_content, config.get('group_chat_prefix')) \
                       or self.check_contain(origin_content, config.get('group_chat_keyword'))
        if ('ALL_GROUP' in config.get('group_name_white_list') or group_name in config.get('group_name_white_list') or self.check_contain(group_name, config.get('group_name_keyword_white_list'))) and match_prefix:
            img_match_prefix = self.check_prefix(content, load_config().get('image_create_prefix'))
            if img_match_prefix:
                content = content.split(img_match_prefix, 1)[1].strip()
                thread_pool.submit(self._do_send_img, content, group_id)
            else:
                thread_pool.submit(self._do_send_group, content, msg, change_setting)

    def send(self, msg, receiver):
        itchat.send(msg, toUserName=receiver)
        logger.info('[WX] sendMsg={}, receiver={}'.format(msg, receiver))

    def _do_send_voice(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                reply_file = super().build_text_to_voice(reply_text)
                itchat.send_file(reply_file, toUserName=reply_user_id)
                logger.info('[WX] sendFile={}, receiver={}'.format(reply_file, reply_user_id))
        except Exception as e:
            logger.exception(e)

    def _do_send_text(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['session_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                self.send(load_config().get("single_chat_reply_prefix") + reply_text, reply_user_id)
        except Exception as e:
            logger.exception(e)

    def _do_send_img(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = 'IMAGE_CREATE'
            img_url = super().build_reply_content(query, context)
            if not img_url:
                return

            # 图片下载
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)

            # 图片发送
            itchat.send_image(image_storage, reply_user_id)
            logger.info('[WX] sendImage, receiver={}'.format(reply_user_id))
        except Exception as e:
            logger.exception(e)

    def _do_send_group(self, query, msg, change_setting=False):
        if not query:
            return
        context = dict()
        group_name = msg['User']['NickName']
        group_id = msg['User']['UserName']
        group_chat_in_one_session = load_config().get('group_chat_in_one_session', [])
        if ('ALL_GROUP' in group_chat_in_one_session or \
                group_name in group_chat_in_one_session or \
                self.check_contain(group_name, group_chat_in_one_session)):
            context['session_id'] = group_id
        else:
            context['session_id'] = msg['ActualUserName']

        if not change_setting:
            reply_text = super().build_reply_content(query, context, msg['ActualNickName'])
        else:
            reply_text = "设置成功"
        if reply_text:
            reply_text = '@' + msg['ActualNickName'] + ' ' + reply_text.strip()
            self.send(load_config().get("group_chat_reply_prefix", "") + reply_text, group_id)

    def check_prefix(self, content, prefix_list):
        for prefix in prefix_list:
            if content.startswith(prefix):
                return prefix
        return None

    def check_contain(self, content, keyword_list):
        if not keyword_list:
            return None
        for ky in keyword_list:
            if content.find(ky) != -1:
                return True
        return None


