"""
钉钉通道接入

@author huiwen
@Date 2023/11/28
"""
import copy
import json
# -*- coding=utf-8 -*-
import logging
import time
import requests

import dingtalk_stream
from dingtalk_stream import AckMessage
from dingtalk_stream.card_replier import AICardReplier
from dingtalk_stream.card_replier import AICardStatus
from dingtalk_stream.card_replier import CardReplier

from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.dingtalk.dingtalk_message import DingTalkMessage
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from common.time_check import time_checker
from config import conf


class CustomAICardReplier(CardReplier):
    def __init__(self, dingtalk_client, incoming_message):
        super(AICardReplier, self).__init__(dingtalk_client, incoming_message)

    def start(
            self,
            card_template_id: str,
            card_data: dict,
            recipients: list = None,
            support_forward: bool = True,
    ) -> str:
        """
        AI卡片的创建接口
        :param support_forward:
        :param recipients:
        :param card_template_id:
        :param card_data:
        :return:
        """
        card_data_with_status = copy.deepcopy(card_data)
        card_data_with_status["flowStatus"] = AICardStatus.PROCESSING
        return self.create_and_send_card(
            card_template_id,
            card_data_with_status,
            at_sender=True,
            at_all=False,
            recipients=recipients,
            support_forward=support_forward,
        )


# 对 AICardReplier 进行猴子补丁
AICardReplier.start = CustomAICardReplier.start


def _check(func):
    def wrapper(self, cmsg: DingTalkMessage):
        msgId = cmsg.msg_id
        if msgId in self.receivedMsgs:
            logger.info("DingTalk message {} already received, ignore".format(msgId))
            return
        self.receivedMsgs[msgId] = True
        create_time = cmsg.create_time  # 消息时间戳
        if conf().get("hot_reload") == True and int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[DingTalk] History message {} skipped".format(msgId))
            return
        if cmsg.my_msg and not cmsg.is_group:
            logger.debug("[DingTalk] My message {} skipped".format(msgId))
            return
        return func(self, cmsg)

    return wrapper


@singleton
class DingTalkChanel(ChatChannel, dingtalk_stream.ChatbotHandler):
    dingtalk_client_id = conf().get('dingtalk_client_id')
    dingtalk_client_secret = conf().get('dingtalk_client_secret')

    def setup_logger(self):
        logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def __init__(self):
        super().__init__()
        super(dingtalk_stream.ChatbotHandler, self).__init__()
        self.logger = self.setup_logger()
        # 历史消息id暂存，用于幂等控制
        self.receivedMsgs = ExpiredDict(conf().get("expires_in_seconds", 3600))
        logger.info("[DingTalk] client_id={}, client_secret={} ".format(
            self.dingtalk_client_id, self.dingtalk_client_secret))
        # 无需群校验和前缀
        conf()["group_name_white_list"] = ["ALL_GROUP"]
        # 单聊无需前缀
        conf()["single_chat_prefix"] = [""]
        # Access token cache
        self._access_token = None
        self._access_token_expires_at = 0
        # Robot code cache (extracted from incoming messages)
        self._robot_code = None

    def startup(self):
        credential = dingtalk_stream.Credential(self.dingtalk_client_id, self.dingtalk_client_secret)
        client = dingtalk_stream.DingTalkStreamClient(credential)
        client.register_callback_handler(dingtalk_stream.chatbot.ChatbotMessage.TOPIC, self)
        client.start_forever()
    
    def get_access_token(self):
        """
        获取企业内部应用的 access_token
        文档: https://open.dingtalk.com/document/orgapp/obtain-orgapp-token
        """
        current_time = time.time()
        
        # 如果 token 还没过期，直接返回缓存的 token
        if self._access_token and current_time < self._access_token_expires_at:
            return self._access_token
        
        # 获取新的 access_token
        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        headers = {"Content-Type": "application/json"}
        data = {
            "appKey": self.dingtalk_client_id,
            "appSecret": self.dingtalk_client_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if response.status_code == 200 and "accessToken" in result:
                self._access_token = result["accessToken"]
                # Token 有效期为 2 小时，提前 5 分钟刷新
                self._access_token_expires_at = current_time + result.get("expireIn", 7200) - 300
                logger.info("[DingTalk] Access token refreshed successfully")
                return self._access_token
            else:
                logger.error(f"[DingTalk] Failed to get access token: {result}")
                return None
        except Exception as e:
            logger.error(f"[DingTalk] Error getting access token: {e}")
            return None
    
    def send_single_message(self, user_id: str, content: str, robot_code: str) -> bool:
        """
        Send message to single user (private chat)
        API: https://open.dingtalk.com/document/orgapp/chatbots-send-one-on-one-chat-messages-in-batches
        """
        access_token = self.get_access_token()
        if not access_token:
            logger.error("[DingTalk] Failed to send single message: Access token not available.")
            return False

        if not robot_code:
            logger.error("[DingTalk] Cannot send single message: robot_code is required")
            return False

        url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
        headers = {
            "x-acs-dingtalk-access-token": access_token,
            "Content-Type": "application/json"
        }
        data = {
            "msgParam": json.dumps({"content": content}),
            "msgKey": "sampleText",
            "userIds": [user_id],
            "robotCode": robot_code
        }

        logger.info(f"[DingTalk] Sending single message to user {user_id} with robot_code {robot_code}")
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if response.status_code == 200 and result.get("processQueryKey"):
                logger.info(f"[DingTalk] Single message sent successfully to {user_id}")
                return True
            else:
                logger.error(f"[DingTalk] Failed to send single message: {result}")
                return False
        except Exception as e:
            logger.error(f"[DingTalk] Error sending single message: {e}")
            return False
    
    def send_group_message(self, conversation_id: str, content: str, robot_code: str = None):
        """
        主动发送群消息
        文档: https://open.dingtalk.com/document/orgapp/the-robot-sends-a-group-message
        
        Args:
            conversation_id: 会话ID (openConversationId)
            content: 消息内容
            robot_code: 机器人编码，默认使用 dingtalk_client_id
        """
        access_token = self.get_access_token()
        if not access_token:
            logger.error("[DingTalk] Cannot send group message: no access token")
            return False
        
        # Validate robot_code
        if not robot_code:
            logger.error("[DingTalk] Cannot send group message: robot_code is required")
            return False
        
        url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"
        headers = {
            "x-acs-dingtalk-access-token": access_token,
            "Content-Type": "application/json"
        }
        data = {
            "msgParam": json.dumps({"content": content}),
            "msgKey": "sampleText",
            "openConversationId": conversation_id,
            "robotCode": robot_code
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                logger.info(f"[DingTalk] Group message sent successfully to {conversation_id}")
                return True
            else:
                logger.error(f"[DingTalk] Failed to send group message: {result}")
                return False
        except Exception as e:
            logger.error(f"[DingTalk] Error sending group message: {e}")
            return False

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        try:
            incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
            
            # Debug: 打印完整的 event 数据
            logger.info(f"[DingTalk] ===== Incoming Message Debug =====")
            logger.info(f"[DingTalk] callback.data keys: {callback.data.keys() if hasattr(callback.data, 'keys') else 'N/A'}")
            logger.info(f"[DingTalk] incoming_message attributes: {dir(incoming_message)}")
            logger.info(f"[DingTalk] robot_code: {getattr(incoming_message, 'robot_code', 'N/A')}")
            logger.info(f"[DingTalk] chatbot_corp_id: {getattr(incoming_message, 'chatbot_corp_id', 'N/A')}")
            logger.info(f"[DingTalk] chatbot_user_id: {getattr(incoming_message, 'chatbot_user_id', 'N/A')}")
            logger.info(f"[DingTalk] conversation_id: {getattr(incoming_message, 'conversation_id', 'N/A')}")
            logger.info(f"[DingTalk] Raw callback.data: {callback.data}")
            logger.info(f"[DingTalk] =====================================")
            
            image_download_handler = self  # 传入方法所在的类实例
            dingtalk_msg = DingTalkMessage(incoming_message, image_download_handler)

            if dingtalk_msg.is_group:
                self.handle_group(dingtalk_msg)
            else:
                self.handle_single(dingtalk_msg)
            return AckMessage.STATUS_OK, 'OK'
        except Exception as e:
            logger.error(f"dingtalk process error={e}")
            return AckMessage.STATUS_SYSTEM_EXCEPTION, 'ERROR'

    @time_checker
    @_check
    def handle_single(self, cmsg: DingTalkMessage):
        # 处理单聊消息
        if cmsg.ctype == ContextType.VOICE:
            logger.debug("[DingTalk]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[DingTalk]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE_CREATE:
            logger.debug("[DingTalk]receive image create msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[DingTalk]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[DingTalk]receive text msg: {}".format(cmsg.content))
        else:
            logger.debug("[DingTalk]receive other msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        if context:
            self.produce(context)


    @time_checker
    @_check
    def handle_group(self, cmsg: DingTalkMessage):
        # 处理群聊消息
        if cmsg.ctype == ContextType.VOICE:
            logger.debug("[DingTalk]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[DingTalk]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE_CREATE:
            logger.debug("[DingTalk]receive image create msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[DingTalk]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[DingTalk]receive text msg: {}".format(cmsg.content))
        else:
            logger.debug("[DingTalk]receive other msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        context['no_need_at'] = True
        if context:
            self.produce(context)


    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        
        # Check if msg exists (for scheduled tasks, msg might be None)
        msg = context.kwargs.get('msg')
        if msg is None:
            # 定时任务场景：使用主动发送 API
            is_group = context.get("isgroup", False)
            logger.info(f"[DingTalk] Sending scheduled task message to {receiver} (is_group={is_group})")
            
            # 使用缓存的 robot_code 或配置的值
            robot_code = self._robot_code or conf().get("dingtalk_robot_code")
            logger.info(f"[DingTalk] Using robot_code: {robot_code}, cached: {self._robot_code}, config: {conf().get('dingtalk_robot_code')}")
            
            if not robot_code:
                logger.error(f"[DingTalk] Cannot send scheduled task: robot_code not available. Please send at least one message to the bot first, or configure dingtalk_robot_code in config.json")
                return
            
            # 根据是否群聊选择不同的 API
            if is_group:
                success = self.send_group_message(receiver, reply.content, robot_code)
            else:
                # 单聊场景：尝试从 context 中获取 dingtalk_sender_staff_id
                sender_staff_id = context.get("dingtalk_sender_staff_id")
                if not sender_staff_id:
                    logger.error(f"[DingTalk] Cannot send single chat scheduled message: sender_staff_id not available in context")
                    return
                
                logger.info(f"[DingTalk] Sending single message to staff_id: {sender_staff_id}")
                success = self.send_single_message(sender_staff_id, reply.content, robot_code)
            
            if not success:
                logger.error(f"[DingTalk] Failed to send scheduled task message")
            return
        
        # 从正常消息中提取并缓存 robot_code
        if hasattr(msg, 'robot_code'):
            robot_code = msg.robot_code
            if robot_code and robot_code != self._robot_code:
                self._robot_code = robot_code
                logger.info(f"[DingTalk] Cached robot_code: {robot_code}")
        
        isgroup = msg.is_group
        incoming_message = msg.incoming_message

        if conf().get("dingtalk_card_enabled"):
            logger.info("[Dingtalk] sendMsg={}, receiver={}".format(reply, receiver))
            def reply_with_text():
                self.reply_text(reply.content, incoming_message)
            def reply_with_at_text():
                self.reply_text("📢 您有一条新的消息，请查看。", incoming_message)
            def reply_with_ai_markdown():
                button_list, markdown_content = self.generate_button_markdown_content(context, reply)
                self.reply_ai_markdown_button(incoming_message, markdown_content, button_list, "", "📌 内容由AI生成", "",[incoming_message.sender_staff_id])

            if reply.type in [ReplyType.IMAGE_URL, ReplyType.IMAGE, ReplyType.TEXT]:
                if isgroup:
                    reply_with_ai_markdown()
                    reply_with_at_text()
                else:
                    reply_with_ai_markdown()
            else:
                # 暂不支持其它类型消息回复
                reply_with_text()
        else:
            self.reply_text(reply.content, incoming_message)


    def generate_button_markdown_content(self, context, reply):
        image_url = context.kwargs.get("image_url")
        promptEn = context.kwargs.get("promptEn")
        reply_text = reply.content
        button_list = []
        markdown_content = f"""
{reply.content}
                                """
        if image_url is not None and promptEn is not None:
            button_list = [
                {"text": "查看原图", "url": image_url, "iosUrl": image_url, "color": "blue"}
            ]
            markdown_content = f"""
{promptEn}

!["图片"]({image_url})

{reply_text}

                                """
        logger.debug(f"[Dingtalk] generate_button_markdown_content, button_list={button_list} , markdown_content={markdown_content}")

        return button_list, markdown_content
