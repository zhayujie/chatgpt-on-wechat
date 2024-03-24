from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from linkai import LinkAIClient, PushMsg
from config import conf, pconf, plugin_config
from plugins import PluginManager


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

    def on_config(self, config: dict):
        if not self.client_id:
            return
        logger.info(f"从控制台加载配置: {config}")
        local_config = conf()
        for key in local_config.keys():
            if config.get(key) is not None:
                local_config[key] = config.get(key)
        if config.get("reply_voice_mode"):
            if config.get("reply_voice_mode") == "voice_reply_voice":
                local_config["voice_reply_voice"] = True
            elif config.get("reply_voice_mode") == "always_reply_voice":
                local_config["always_reply_voice"] = True
        # if config.get("admin_password") and plugin_config["Godcmd"]:
        #     plugin_config["Godcmd"]["password"] = config.get("admin_password")
        #     PluginManager().instances["Godcmd"].reload()
        # if config.get("group_app_map") and pconf("linkai"):
        #     local_group_map = {}
        #     for mapping in config.get("group_app_map"):
        #         local_group_map[mapping.get("group_name")] = mapping.get("app_code")
        #     pconf("linkai")["group_app_map"] = local_group_map
        #     PluginManager().instances["linkai"].reload()


def start(channel):
    global chat_client
    chat_client = ChatClient(api_key=conf().get("linkai_api_key"),
                        host="link-ai.chat", channel=channel)
    chat_client.start()
