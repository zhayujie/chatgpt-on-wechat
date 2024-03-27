from wechatpy.enterprise import WeChatClient

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir


class WechatComServiceMessage(ChatMessage):
    def __init__(self, msg, client: WeChatClient = None, is_group=False):
        self.is_group = is_group
        self.msg_id = msg['msgid']
        self.external_userid = msg['external_userid']
        self.create_time = msg['send_time']
        self.origin = msg['origin']
        self.msgtype = msg['msgtype']
        self.open_kfid = msg['open_kfid']

        if self.msgtype == "text":
            self.content = msg['text']['content']
            self.ctype = ContextType.TEXT
        elif self.msgtype == "image":
            self.ctype = ContextType.IMAGE
            # 实现图像消息的处理逻辑
            self.content = TmpDir().path() + msg.get("image", {}).get("media_id", "") + "." + 'jpg'  # 假设图片格式为jpg

            def download_image():
                # 下载图片逻辑
                response = client.media.download(msg.get("image", {}).get("media_id", ""))
                if response.status_code == 200:
                    with open(self.content, "wb") as f:
                        f.write(response.content)
                else:
                    logger.info(f"[wechatcom_copy] Failed to download image file, {response.content}")

            # download_image()
            self._prepare_fn = download_image
        elif self.msgtype == "voice":
            self.ctype = ContextType.VOICE
            self.content = TmpDir().path() + msg.get("voice", {}).get("media_id", "") + "." + 'mp3'  # content直接存临时目录路径

            def download_voice():
                # 如果响应状态码是200，则将响应内容写入本地文件
                response = client.media.download(msg.get("voice", {}).get("media_id", ""))
                if response.status_code == 200:
                    with open(self.content, "wb") as f:
                        f.write(response.content)
                else:
                    logger.info(f"[wechatcom_copy] Failed to download voice file, {response.content}")

            # download_voice()
            self._prepare_fn = download_voice
        # 可以根据需要添加更多消息类型的处理
        self.from_user_id = self.external_userid
        self.to_user_id = self.open_kfid
        self.other_user_id = self.external_userid
