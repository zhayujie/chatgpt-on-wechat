# encoding:utf-8

import plugins
from plugins import *

@plugins.register(
    name="CustomDifyApp",
    desire_priority=0,
    hidden=True,
    enabled=True,
    desc="根据群聊环境自动选择相应的Dify应用",
    version="0.2",
    author="zexin.li, hanfangyuan",
)
class CustomDifyApp(Plugin):

    def __init__(self):
        super().__init__()
        try:
            # 加载配置文件
            self.config = super().load_config()
            # 单聊配置初始化为None
            self.single_chat_conf = None
            if self.config is None:
                logger.info("[CustomDifyApp] config is None")
                return
            # 初始化单聊配置
            self._init_single_chat_conf()
            logger.info("[CustomDifyApp] inited")
            # 注册事件处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[CustomDifyApp]初始化异常：{e}")
            raise "[CustomDifyApp] init failed, ignore "

    def _init_single_chat_conf(self):
        # 遍历配置，找到用于单聊的配置
        for dify_app_dict in self.config:
            if "use_on_single_chat" in dify_app_dict and dify_app_dict["use_on_single_chat"]:
                self.single_chat_conf = dify_app_dict
                break

    def on_handle_context(self, e_context: EventContext):
        try:
            if self.config is None:
                return

            context = e_context["context"]
            dify_app_conf = None
            # 判断是群聊还是单聊
            if context.get("isgroup", False):
                # 群聊情况
                group_name = context["group_name"]
                # 遍历配置，找到匹配的群名关键词
                for conf in self.config:
                    if "group_name_keywords" in conf:
                        if any(keyword in group_name for keyword in conf["group_name_keywords"]):
                            dify_app_conf = conf
                            break
            else:
                # 单聊情况，使用预设的单聊配置
                dify_app_conf = self.single_chat_conf

            # 如果没有找到匹配的配置，直接返回
            if dify_app_conf is None:
                return
            # 检查配置是否完整
            if not (dify_app_conf.get("app_type") and dify_app_conf.get("api_base") and dify_app_conf.get("api_key")):
                logger.warning(f"[CustomDifyApp] dify app config is invalid: {dify_app_conf}")
                return

            # 使用找到的配置
            logger.debug(f"use dify app: {dify_app_conf['app_name']}")
            context["dify_app_type"] = dify_app_conf["app_type"]
            context["dify_api_base"] = dify_app_conf["api_base"]
            context["dify_api_key"] = dify_app_conf["api_key"]
        except Exception as e:
            logger.error(f"[CustomDifyApp] on_handle_context error: {e}")
