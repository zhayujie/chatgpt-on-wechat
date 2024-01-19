from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from linkai import LinkAIClient, PushMsg
from config import conf

chat_client: LinkAIClient

class ChatClient(LinkAIClient):
    def __init__(self, api_key, host, channel):
        super().__init__(api_key, host)
        self.channel = channel
        self.client_type = channel.channel_type

    def on_message(self, push_msg: PushMsg):
        session_id = push_msg.session_id
        msg_content = push_msg.msg_content
        logger.info(f"receive msg push, session_id={session_id}, msg_content={msg_content}")
        context = Context()
        context.type = ContextType.TEXT
        context["receiver"] = session_id
        context["isgroup"] = push_msg.is_group
        self.channel.send(Reply(ReplyType.TEXT, content=msg_content), context)


def start(channel):
    global chat_client
    chat_client = ChatClient(api_key=conf().get("linkai_api_key"),
                        host="link-ai.chat", channel=channel)
    chat_client.start()
