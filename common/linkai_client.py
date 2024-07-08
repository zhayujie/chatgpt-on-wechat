from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from linkai import LinkAIClient, PushMsg
from config import conf, pconf, plugin_config, available_setting
from plugins import PluginManager
import time


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
        logger.info(f"[LinkAI] 从客户端管理加载远程配置: {config}")
        if config.get("enabled") != "Y":
            return

        local_config = conf()
        for key in config.keys():
            if key in available_setting and config.get(key) is not None:
                local_config[key] = config.get(key)
        # 语音配置
        reply_voice_mode = config.get("reply_voice_mode")
        if reply_voice_mode:
            if reply_voice_mode == "voice_reply_voice":
                local_config["voice_reply_voice"] = True
            elif reply_voice_mode == "always_reply_voice":
                local_config["always_reply_voice"] = True

        if config.get("admin_password"):
            if not plugin_config.get("Godcmd"):
                plugin_config["Godcmd"] = {"password": config.get("admin_password"), "admin_users": []}
            else:
                plugin_config["Godcmd"]["password"] = config.get("admin_password")
            PluginManager().instances["GODCMD"].reload()

        if config.get("group_app_map") and pconf("linkai"):
            local_group_map = {}
            for mapping in config.get("group_app_map"):
                local_group_map[mapping.get("group_name")] = mapping.get("app_code")
            pconf("linkai")["group_app_map"] = local_group_map
            PluginManager().instances["LINKAI"].reload()

        if config.get("text_to_image") and config.get("text_to_image") == "midjourney" and pconf("linkai"):
            if pconf("linkai")["midjourney"]:
                pconf("linkai")["midjourney"]["enabled"] = True
                pconf("linkai")["midjourney"]["use_image_create_prefix"] = True
        elif config.get("text_to_image") and config.get("text_to_image") in ["dall-e-2", "dall-e-3"]:
            if pconf("linkai")["midjourney"]:
                pconf("linkai")["midjourney"]["use_image_create_prefix"] = False


def start(channel):
    global chat_client
    chat_client = ChatClient(api_key=conf().get("linkai_api_key"), host="", channel=channel)
    chat_client.config = _build_config()
    chat_client.start()
    time.sleep(1.5)
    if chat_client.client_id:
        logger.info("[LinkAI] 可前往控制台进行线上登录和配置：https://link-ai.tech/console/clients")


def _build_config():
    local_conf = conf()
    config = {
        "linkai_app_code": local_conf.get("linkai_app_code"),
        "single_chat_prefix": local_conf.get("single_chat_prefix"),
        "single_chat_reply_prefix": local_conf.get("single_chat_reply_prefix"),
        "single_chat_reply_suffix": local_conf.get("single_chat_reply_suffix"),
        "group_chat_prefix": local_conf.get("group_chat_prefix"),
        "group_chat_reply_prefix": local_conf.get("group_chat_reply_prefix"),
        "group_chat_reply_suffix": local_conf.get("group_chat_reply_suffix"),
        "group_name_white_list": local_conf.get("group_name_white_list"),
        "nick_name_black_list": local_conf.get("nick_name_black_list"),
        "speech_recognition": "Y" if local_conf.get("speech_recognition") else "N",
        "text_to_image": local_conf.get("text_to_image"),
        "image_create_prefix": local_conf.get("image_create_prefix")
    }
    if local_conf.get("always_reply_voice"):
        config["reply_voice_mode"] = "always_reply_voice"
    elif local_conf.get("voice_reply_voice"):
        config["reply_voice_mode"] = "voice_reply_voice"
    if pconf("linkai"):
        config["group_app_map"] = pconf("linkai").get("group_app_map")
    if plugin_config.get("Godcmd"):
        config["admin_password"] = plugin_config.get("Godcmd").get("password")
    return config
