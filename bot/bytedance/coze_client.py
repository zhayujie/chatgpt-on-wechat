import logging
import os
import time
from typing import List
from bot.bytedance.coze_session import CozeSession
from pathlib import Path
from cozepy import Coze, TokenAuth, Message, File, MessageContentType, MessageRole, MessageObjectString, \
    MessageObjectStringType


class CozeClient(object):
    def __init__(self, coze_api_key, base_url: str):
        self.coze_api_key = coze_api_key
        self.base_url = base_url
        self.coze = Coze(base_url=base_url,
                         auth=TokenAuth(token=coze_api_key))

    def file_upload(self, path: str) -> File:
        return self.coze.files.upload(file=Path(path))

    def _send_chat(self, bot_id: str,
                   user_id: str, additional_messages: List[Message], session: CozeSession):
        conversation_id = None
        if session.get_conversation_id() is not None:
            conversation_id = session.get_conversation_id()
        chat_poll = self.coze.chat.create_and_poll(
            bot_id=bot_id,
            user_id=user_id,
            conversation_id=conversation_id,
            additional_messages=additional_messages
        )
        message_list = chat_poll.messages
        for message in message_list:
            logging.debug('got message:', message.content)
        return message_list

    def create_chat_message(self, bot_id: str, query: str, additional_messages: List[Message], session: CozeSession):
        if additional_messages is None:
            additional_messages = [Message.build_user_question_text(query)]
        else:
            additional_messages.append(Message.build_user_question_text(query))
        return self._send_chat(bot_id, session.get_user_id(), additional_messages, session)

    def create_message(self, file: File) -> Message:

        message_object_string = None
        if self.is_image(file.file_name):
            message_object_string = MessageObjectString.build_image(file.id)
        else:
            message_object_string = MessageObjectString.build_file(file.id)
        return Message.build_user_question_objects([message_object_string])

    def is_image(self, filepath: str):
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        extension = os.path.splitext(filepath)[1].lower()
        return extension in valid_extensions
