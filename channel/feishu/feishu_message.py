from bridge.context import ContextType
from channel.chat_message import ChatMessage
import json
import requests
from common.log import logger
from common.tmp_dir import TmpDir
from common import utils


class FeishuMessage(ChatMessage):
    def __init__(self, event: dict, is_group=False, access_token=None):
        super().__init__(event)
        msg = event.get("message")
        sender = event.get("sender")
        self.access_token = access_token
        self.msg_id = msg.get("message_id")
        self.create_time = msg.get("create_time")
        self.is_group = is_group
        msg_type = msg.get("message_type")

        if msg_type == "text":
            self.ctype = ContextType.TEXT
            content = json.loads(msg.get('content'))
            self.content = content.get("text").strip()
        elif msg_type == "file":
            self.ctype = ContextType.FILE
            content = json.loads(msg.get("content"))
            file_key = content.get("file_key")
            file_name = content.get("file_name")

            self.content = TmpDir().path() + file_key + "." + utils.get_path_suffix(file_name)

            def _download_file():
                # 如果响应状态码是200，则将响应内容写入本地文件
                url = f"https://open.feishu.cn/open-apis/im/v1/messages/{self.msg_id}/resources/{file_key}"
                headers = {
                    "Authorization": "Bearer " + access_token,
                }
                params = {
                    "type": "file"
                }
                response = requests.get(url=url, headers=headers, params=params)
                if response.status_code == 200:
                    with open(self.content, "wb") as f:
                        f.write(response.content)
                else:
                    logger.info(f"[FeiShu] Failed to download file, key={file_key}, res={response.text}")
            self._prepare_fn = _download_file

        # elif msg.type == "voice":
        #     self.ctype = ContextType.VOICE
        #     self.content = TmpDir().path() + msg.media_id + "." + msg.format  # content直接存临时目录路径
        #
        #     def download_voice():
        #         # 如果响应状态码是200，则将响应内容写入本地文件
        #         response = client.media.download(msg.media_id)
        #         if response.status_code == 200:
        #             with open(self.content, "wb") as f:
        #                 f.write(response.content)
        #         else:
        #             logger.info(f"[wechatcom] Failed to download voice file, {response.content}")
        #
        #     self._prepare_fn = download_voice
        # elif msg.type == "image":
        #     self.ctype = ContextType.IMAGE
        #     self.content = TmpDir().path() + msg.media_id + ".png"  # content直接存临时目录路径
        #
        #     def download_image():
        #         # 如果响应状态码是200，则将响应内容写入本地文件
        #         response = client.media.download(msg.media_id)
        #         if response.status_code == 200:
        #             with open(self.content, "wb") as f:
        #                 f.write(response.content)
        #         else:
        #             logger.info(f"[wechatcom] Failed to download image file, {response.content}")
        #
        #     self._prepare_fn = download_image
        else:
            raise NotImplementedError("Unsupported message type: Type:{} ".format(msg_type))

        self.from_user_id = sender.get("sender_id").get("open_id")
        self.to_user_id = event.get("app_id")
        if is_group:
            # 群聊
            self.other_user_id = msg.get("chat_id")
            self.actual_user_id = self.from_user_id
            self.content = self.content.replace("@_user_1", "").strip()
            self.actual_user_nickname = ""
        else:
            # 私聊
            self.other_user_id = self.from_user_id
            self.actual_user_id = self.from_user_id
