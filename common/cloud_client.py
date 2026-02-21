"""
Cloud management client for connecting to the LinkAI control console.

Handles remote configuration sync, message push, and skill management
via the LinkAI socket protocol.
"""

from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from linkai import LinkAIClient, PushMsg
from config import conf, pconf, plugin_config, available_setting, write_plugin_config, get_root
from plugins import PluginManager
import threading
import time
import json
import os


chat_client: LinkAIClient


class CloudClient(LinkAIClient):
    def __init__(self, api_key: str, channel, host: str = ""):
        super().__init__(api_key, host)
        self.channel = channel
        self.client_type = channel.channel_type
        self.channel_mgr = None
        self._skill_service = None
        self._memory_service = None
        self._chat_service = None

    @property
    def skill_service(self):
        """Lazy-init SkillService so it is available once SkillManager exists."""
        if self._skill_service is None:
            try:
                from agent.skills.manager import SkillManager
                from agent.skills.service import SkillService
                from config import conf
                from common.utils import expand_path
                workspace_root = expand_path(conf().get("agent_workspace", "~/cow"))
                manager = SkillManager(custom_dir=os.path.join(workspace_root, "skills"))
                self._skill_service = SkillService(manager)
                logger.debug("[CloudClient] SkillService initialised")
            except Exception as e:
                logger.error(f"[CloudClient] Failed to init SkillService: {e}")
        return self._skill_service

    @property
    def memory_service(self):
        """Lazy-init MemoryService."""
        if self._memory_service is None:
            try:
                from agent.memory.service import MemoryService
                from config import conf
                from common.utils import expand_path
                workspace_root = expand_path(conf().get("agent_workspace", "~/cow"))
                self._memory_service = MemoryService(workspace_root)
                logger.debug("[CloudClient] MemoryService initialised")
            except Exception as e:
                logger.error(f"[CloudClient] Failed to init MemoryService: {e}")
        return self._memory_service

    @property
    def chat_service(self):
        """Lazy-init ChatService (requires AgentBridge via Bridge singleton)."""
        if self._chat_service is None:
            try:
                from agent.chat.service import ChatService
                from bridge.bridge import Bridge
                agent_bridge = Bridge().get_agent_bridge()
                self._chat_service = ChatService(agent_bridge)
                logger.debug("[CloudClient] ChatService initialised")
            except Exception as e:
                logger.error(f"[CloudClient] Failed to init ChatService: {e}")
        return self._chat_service

    # ------------------------------------------------------------------
    # message push callback
    # ------------------------------------------------------------------
    def on_message(self, push_msg: PushMsg):
        session_id = push_msg.session_id
        msg_content = push_msg.msg_content
        logger.info(f"receive msg push, session_id={session_id}, msg_content={msg_content}")
        context = Context()
        context.type = ContextType.TEXT
        context["receiver"] = session_id
        context["isgroup"] = push_msg.is_group
        self.channel.send(Reply(ReplyType.TEXT, content=msg_content), context)

    # ------------------------------------------------------------------
    # config callback
    # ------------------------------------------------------------------
    def on_config(self, config: dict):
        if not self.client_id:
            return
        logger.info(f"[CloudClient] Loading remote config: {config}")
        if config.get("enabled") != "Y":
            return

        local_config = conf()
        need_restart_channel = False

        for key in config.keys():
            if key in available_setting and config.get(key) is not None:
                local_config[key] = config.get(key)

        # Voice settings
        reply_voice_mode = config.get("reply_voice_mode")
        if reply_voice_mode:
            if reply_voice_mode == "voice_reply_voice":
                local_config["voice_reply_voice"] = True
                local_config["always_reply_voice"] = False
            elif reply_voice_mode == "always_reply_voice":
                local_config["always_reply_voice"] = True
                local_config["voice_reply_voice"] = True
            elif reply_voice_mode == "no_reply_voice":
                local_config["always_reply_voice"] = False
                local_config["voice_reply_voice"] = False

        # Model configuration
        if config.get("model"):
            local_config["model"] = config.get("model")

        # Channel configuration
        if config.get("channelType"):
            if local_config.get("channel_type") != config.get("channelType"):
                local_config["channel_type"] = config.get("channelType")
                need_restart_channel = True

        # Channel-specific app credentials
        current_channel_type = local_config.get("channel_type", "")

        if config.get("app_id") is not None:
            if current_channel_type == "feishu":
                if local_config.get("feishu_app_id") != config.get("app_id"):
                    local_config["feishu_app_id"] = config.get("app_id")
                    need_restart_channel = True
            elif current_channel_type == "dingtalk":
                if local_config.get("dingtalk_client_id") != config.get("app_id"):
                    local_config["dingtalk_client_id"] = config.get("app_id")
                    need_restart_channel = True
            elif current_channel_type in ("wechatmp", "wechatmp_service"):
                if local_config.get("wechatmp_app_id") != config.get("app_id"):
                    local_config["wechatmp_app_id"] = config.get("app_id")
                    need_restart_channel = True
            elif current_channel_type == "wechatcom_app":
                if local_config.get("wechatcomapp_agent_id") != config.get("app_id"):
                    local_config["wechatcomapp_agent_id"] = config.get("app_id")
                    need_restart_channel = True

        if config.get("app_secret"):
            if current_channel_type == "feishu":
                if local_config.get("feishu_app_secret") != config.get("app_secret"):
                    local_config["feishu_app_secret"] = config.get("app_secret")
                    need_restart_channel = True
            elif current_channel_type == "dingtalk":
                if local_config.get("dingtalk_client_secret") != config.get("app_secret"):
                    local_config["dingtalk_client_secret"] = config.get("app_secret")
                    need_restart_channel = True
            elif current_channel_type in ("wechatmp", "wechatmp_service"):
                if local_config.get("wechatmp_app_secret") != config.get("app_secret"):
                    local_config["wechatmp_app_secret"] = config.get("app_secret")
                    need_restart_channel = True
            elif current_channel_type == "wechatcom_app":
                if local_config.get("wechatcomapp_secret") != config.get("app_secret"):
                    local_config["wechatcomapp_secret"] = config.get("app_secret")
                    need_restart_channel = True

        if config.get("admin_password"):
            if not pconf("Godcmd"):
                write_plugin_config({"Godcmd": {"password": config.get("admin_password"), "admin_users": []}})
            else:
                pconf("Godcmd")["password"] = config.get("admin_password")
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

        # Save configuration to config.json file
        self._save_config_to_file(local_config)

        if need_restart_channel:
            self._restart_channel(local_config.get("channel_type", ""))

    # ------------------------------------------------------------------
    # skill callback
    # ------------------------------------------------------------------
    def on_skill(self, data: dict) -> dict:
        """
        Handle SKILL messages from the cloud console.
        Delegates to SkillService.dispatch for the actual operations.

        :param data: message data with 'action', 'clientId', 'payload'
        :return: response dict
        """
        action = data.get("action", "")
        payload = data.get("payload")
        logger.info(f"[CloudClient] on_skill: action={action}")

        svc = self.skill_service
        if svc is None:
            return {"action": action, "code": 500, "message": "SkillService not available", "payload": None}

        return svc.dispatch(action, payload)

    # ------------------------------------------------------------------
    # memory callback
    # ------------------------------------------------------------------
    def on_memory(self, data: dict) -> dict:
        """
        Handle MEMORY messages from the cloud console.
        Delegates to MemoryService.dispatch for the actual operations.

        :param data: message data with 'action', 'clientId', 'payload'
        :return: response dict
        """
        action = data.get("action", "")
        payload = data.get("payload")
        logger.info(f"[CloudClient] on_memory: action={action}")

        svc = self.memory_service
        if svc is None:
            return {"action": action, "code": 500, "message": "MemoryService not available", "payload": None}

        return svc.dispatch(action, payload)

    # ------------------------------------------------------------------
    # chat callback
    # ------------------------------------------------------------------
    def on_chat(self, data: dict, send_chunk_fn):
        """
        Handle CHAT messages from the cloud console.
        Runs the agent in streaming mode and sends chunks back via send_chunk_fn.

        :param data: message data with 'action' and 'payload' (query, session_id)
        :param send_chunk_fn: callable(chunk_data: dict) to send one streaming chunk
        """
        payload = data.get("payload", {})
        query = payload.get("query", "")
        session_id = payload.get("session_id", "cloud_console")
        logger.info(f"[CloudClient] on_chat: session={session_id}, query={query[:80]}")

        svc = self.chat_service
        if svc is None:
            raise RuntimeError("ChatService not available")

        svc.run(query=query, session_id=session_id, send_chunk_fn=send_chunk_fn)

    # ------------------------------------------------------------------
    # channel restart helpers
    # ------------------------------------------------------------------
    def _restart_channel(self, new_channel_type: str):
        """
        Restart the channel via ChannelManager when channel type changes.
        """
        if self.channel_mgr:
            logger.info(f"[CloudClient] Restarting channel to '{new_channel_type}'...")
            threading.Thread(target=self._do_restart_channel, args=(self.channel_mgr, new_channel_type), daemon=True).start()
        else:
            logger.warning("[CloudClient] ChannelManager not available, please restart the application manually")

    def _do_restart_channel(self, mgr, new_channel_type: str):
        """
        Perform the channel restart in a separate thread to avoid blocking the config callback.
        """
        try:
            mgr.restart(new_channel_type)
            # Update the client's channel reference
            if mgr.channel:
                self.channel = mgr.channel
                self.client_type = mgr.channel.channel_type
                logger.info(f"[CloudClient] Channel reference updated to '{new_channel_type}'")
        except Exception as e:
            logger.error(f"[CloudClient] Channel restart failed: {e}")

    # ------------------------------------------------------------------
    # config persistence
    # ------------------------------------------------------------------
    def _save_config_to_file(self, local_config: dict):
        """
        Save configuration to config.json file.
        """
        try:
            config_path = os.path.join(get_root(), "config.json")
            if not os.path.exists(config_path):
                logger.warning(f"[CloudClient] config.json not found at {config_path}, skip saving")
                return

            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)

            file_config.update(dict(local_config))

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(file_config, f, indent=4, ensure_ascii=False)

            logger.info("[CloudClient] Configuration saved to config.json successfully")
        except Exception as e:
            logger.error(f"[CloudClient] Failed to save configuration to config.json: {e}")


def start(channel, channel_mgr=None):
    global chat_client
    chat_client = CloudClient(api_key=conf().get("linkai_api_key"), host=conf().get("cloud_host", ""), channel=channel)
    chat_client.channel_mgr = channel_mgr
    chat_client.config = _build_config()
    chat_client.start()
    time.sleep(1.5)
    if chat_client.client_id:
        logger.info("[CloudClient] Console: https://link-ai.tech/console/clients")


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
        "image_create_prefix": local_conf.get("image_create_prefix"),
        "model": local_conf.get("model"),
        "agent_max_context_turns": local_conf.get("agent_max_context_turns"),
        "agent_max_context_tokens": local_conf.get("agent_max_context_tokens"),
        "agent_max_steps": local_conf.get("agent_max_steps"),
        "channelType": local_conf.get("channel_type"),
    }

    if local_conf.get("always_reply_voice"):
        config["reply_voice_mode"] = "always_reply_voice"
    elif local_conf.get("voice_reply_voice"):
        config["reply_voice_mode"] = "voice_reply_voice"

    if pconf("linkai"):
        config["group_app_map"] = pconf("linkai").get("group_app_map")

    if plugin_config.get("Godcmd"):
        config["admin_password"] = plugin_config.get("Godcmd").get("password")

    # Add channel-specific app credentials
    current_channel_type = local_conf.get("channel_type", "")
    if current_channel_type == "feishu":
        config["app_id"] = local_conf.get("feishu_app_id")
        config["app_secret"] = local_conf.get("feishu_app_secret")
    elif current_channel_type == "dingtalk":
        config["app_id"] = local_conf.get("dingtalk_client_id")
        config["app_secret"] = local_conf.get("dingtalk_client_secret")
    elif current_channel_type in ("wechatmp", "wechatmp_service"):
        config["app_id"] = local_conf.get("wechatmp_app_id")
        config["app_secret"] = local_conf.get("wechatmp_app_secret")
    elif current_channel_type == "wechatcom_app":
        config["app_id"] = local_conf.get("wechatcomapp_agent_id")
        config["app_secret"] = local_conf.get("wechatcomapp_secret")

    return config
