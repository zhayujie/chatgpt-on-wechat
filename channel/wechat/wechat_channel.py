"""
wechat channel
"""
import itchat
import json
from itchat.content import *
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from common.log import logger
from config import conf

thead_pool = ThreadPoolExecutor(max_workers=8)


@itchat.msg_register(TEXT)
def handler_single_msg(msg):
    WechatChannel().handle(msg)


@itchat.msg_register(TEXT, isGroupChat=True)
def handler_group_msg(msg):
    WechatChannel().handle_group(msg)


class WechatChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        # login by scan QRCode
        itchat.auto_login(enableCmdQR=2)

        # start message listener
        itchat.run()

    def handle(self, msg):
        logger.info("[WX]receive msg: " + json.dumps(msg, ensure_ascii=False))
        from_user_id = msg['FromUserName']
        other_user_id = msg['User']['UserName']
        content = msg['Text']
        if from_user_id == other_user_id and \
                self.check_prefix(content, conf().get('group_chat_prefix')):
            str_list = content.split('bot', 1)
            if len(str_list) == 2:
                content = str_list[1].strip()
            thead_pool.submit(self._do_send, content, from_user_id)



    def handle_group(self, msg):
        logger.info("[WX]receive group msg: " + json.dumps(msg, ensure_ascii=False))
        group_id = msg['User']['UserName']
        group_name = msg['User'].get('NickName', None)
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

        config = conf()
        if group_name in config.get('group_name_white_list') \
                and (msg['IsAt'] or self.check_prefix(origin_content, config.get('group_chat_prefix'))):
            thead_pool.submit(self._do_send_group, content, msg)

    def send(self, msg, receiver):
        # time.sleep(random.randint(1, 3))
        logger.info('[WX] sendMsg={}, receiver={}'.format(msg, receiver))
        itchat.send(msg, toUserName=receiver)

    def _do_send(self, send_msg, reply_user_id):
        context = dict()
        context['from_user_id'] = reply_user_id
        content = super().build_reply_content(send_msg, context)
        if content:
            self.send("[bot] " + content, reply_user_id)

    def _do_send_group(self, content, msg):
        context = dict()
        context['from_user_id'] = msg['ActualUserName']
        reply_text = super().build_reply_content(content, context)
        reply_text = '@' + msg['ActualNickName'] + ' ' + reply_text
        if reply_text:
            self.send(reply_text, msg['User']['UserName'])

    def check_prefix(self, content, prefix_list):
        for prefix in prefix_list:
            if content.lower().startswith(prefix):
                return True
        return False

