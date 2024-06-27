import os

import requests
from dingtalk_stream import ChatbotMessage

from bridge.context import ContextType
from channel.chat_message import ChatMessage
# -*- coding=utf-8 -*-
from common.log import logger
from common.tmp_dir import TmpDir


class DingTalkMessage(ChatMessage):
    def __init__(self, event: ChatbotMessage, image_download_handler):
        super().__init__(event)
        self.image_download_handler = image_download_handler
        self.msg_id = event.message_id
        self.message_type = event.message_type
        self.incoming_message = event
        self.sender_staff_id = event.sender_staff_id
        self.other_user_id = event.conversation_id
        self.create_time = event.create_at
        self.image_content = event.image_content
        self.rich_text_content = event.rich_text_content
        if event.conversation_type == "1":
            self.is_group = False
        else:
            self.is_group = True

        if self.message_type == "text":
            self.ctype = ContextType.TEXT

            self.content = event.text.content.strip()
        elif self.message_type == "audio":
            # 钉钉支持直接识别语音，所以此处将直接提取文字，当文字处理
            self.content = event.extensions['content']['recognition'].strip()
            self.ctype = ContextType.TEXT
        elif (self.message_type == 'picture') or (self.message_type == 'richText'):
            self.ctype = ContextType.IMAGE
            # 钉钉图片类型或富文本类型消息处理
            image_list = event.get_image_list()
            if len(image_list) > 0:
                download_code = image_list[0]
                download_url = image_download_handler.get_image_download_url(download_code)
                self.content = download_image_file(download_url, TmpDir().path())
            else:
                logger.debug(f"[Dingtalk] messageType :{self.message_type} , imageList isEmpty")

        if self.is_group:
            self.from_user_id = event.conversation_id
            self.actual_user_id = event.sender_id
            self.is_at = True
        else:
            self.from_user_id = event.sender_id
            self.actual_user_id = event.sender_id
        self.to_user_id = event.chatbot_user_id
        self.other_user_nickname = event.conversation_title


def download_image_file(image_url, temp_dir):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    # 设置代理
    # self.proxies
    # , proxies=self.proxies
    response = requests.get(image_url, headers=headers, stream=True, timeout=60 * 5)
    if response.status_code == 200:

        # 生成文件名
        file_name = image_url.split("/")[-1].split("?")[0]

        # 检查临时目录是否存在，如果不存在则创建
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # 将文件保存到临时目录
        file_path = os.path.join(temp_dir, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return file_path
    else:
        logger.info(f"[Dingtalk] Failed to download image file, {response.content}")
        return None
