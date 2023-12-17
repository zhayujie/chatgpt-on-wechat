from bridge.context import ContextType
from channel.chat_message import ChatMessage
import json
import requests
from common.log import logger
from common.tmp_dir import TmpDir
from common import utils
from dingtalk_stream import ChatbotMessage

class DingTalkMessage(ChatMessage):
    def __init__(self, event: ChatbotMessage):
        super().__init__(event)
        
        self.msg_id = event.message_id
        msg_type = event.message_type
        self.incoming_message =event
        self.sender_staff_id = event.sender_staff_id
        
        self.create_time = event.create_at
        if event.conversation_type=="1":
            self.is_group = False
        else:
            self.is_group = True
        

        if msg_type == "text":
            self.ctype = ContextType.TEXT
            
            self.content = event.text.content.strip()
        
        self.from_user_id = event.sender_id
        self.to_user_id = event.chatbot_user_id
        self.other_user_nickname = event.conversation_title
        
        user_id = event.sender_id
        nickname =event.sender_nick

        

      
