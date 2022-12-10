"""
wechat channel
"""
import itchat
import json
from itchat.content import *
from channel.channel import Channel


@itchat.msg_register([TEXT])
def handler_receive_msg(msg):
    WechatChannel().handle(msg)


class WechatChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        # login by scan QRCode
        itchat.auto_login()

        # start message listener
        itchat.run()

    def handle(self, msg):
        print("handle: ", msg)
        print(json.dumps(msg, ensure_ascii=False))
        from_user_id = msg['FromUserName']
        other_user_id = msg['User']['UserName']
        if from_user_id == other_user_id:
            self.send(super().build_reply_content(msg['Text']), from_user_id)

    def send(self, msg, receiver):
        # time.sleep(random.randint(1, 3))
        print(msg, receiver)
        itchat.send(msg + " [bot]", toUserName=receiver)
