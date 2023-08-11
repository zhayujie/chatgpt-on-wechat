import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import global_config
from plugins import *
from .midjourney import MJBot
from bridge import bridge


@plugins.register(
    name="linkai",
    desc="A plugin that supports knowledge base and midjourney drawing.",
    version="0.1.0",
    author="https://link-ai.tech",
)
class LinkAI(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.config = super().load_config()
        if self.config:
            self.mj_bot = MJBot(self.config.get("midjourney"))
        logger.info("[LinkAI] inited")

    def on_handle_context(self, e_context: EventContext):
        """
        消息处理逻辑
        :param e_context: 消息上下文
        """
        if not self.config:
            return

        context = e_context['context']
        if context.type not in [ContextType.TEXT, ContextType.IMAGE, ContextType.IMAGE_CREATE]:
            # filter content no need solve
            return

        mj_type = self.mj_bot.judge_mj_task_type(e_context)
        if mj_type:
            # MJ作图任务处理
            self.mj_bot.process_mj_task(mj_type, e_context)
            return

        if context.content.startswith(f"{_get_trigger_prefix()}linkai"):
            # 应用管理功能
            self._process_admin_cmd(e_context)
            return

        if self._is_chat_task(e_context):
            # 文本对话任务处理
            self._process_chat_task(e_context)

    # 插件管理功能
    def _process_admin_cmd(self, e_context: EventContext):
        context = e_context['context']
        cmd = context.content.split()
        if len(cmd) == 1 or (len(cmd) == 2 and cmd[1] == "help"):
            _set_reply_text(self.get_help_text(verbose=True), e_context, level=ReplyType.INFO)
            return

        if len(cmd) == 2 and (cmd[1] == "open" or cmd[1] == "close"):
            # 知识库开关指令
            if not _is_admin(e_context):
                _set_reply_text("需要管理员权限执行", e_context, level=ReplyType.ERROR)
                return
            is_open = True
            tips_text = "开启"
            if cmd[1] == "close":
                tips_text = "关闭"
                is_open = False
            conf()["use_linkai"] = is_open
            bridge.Bridge().reset_bot()
            _set_reply_text(f"知识库功能已{tips_text}", e_context, level=ReplyType.INFO)
            return

        if len(cmd) == 3 and cmd[1] == "app":
            # 知识库应用切换指令
            if not context.kwargs.get("isgroup"):
                _set_reply_text("该指令需在群聊中使用", e_context, level=ReplyType.ERROR)
                return
            if not _is_admin(e_context):
                _set_reply_text("需要管理员权限执行", e_context, level=ReplyType.ERROR)
                return
            app_code = cmd[2]
            group_name = context.kwargs.get("msg").from_user_nickname
            group_mapping = self.config.get("group_app_map")
            if group_mapping:
                group_mapping[group_name] = app_code
            else:
                self.config["group_app_map"] = {group_name: app_code}
            # 保存插件配置
            super().save_config(self.config)
            _set_reply_text(f"应用设置成功: {app_code}", e_context, level=ReplyType.INFO)
        else:
            _set_reply_text(f"指令错误，请输入{_get_trigger_prefix()}linkai help 获取帮助", e_context,
                            level=ReplyType.INFO)
            return

    # LinkAI 对话任务处理
    def _is_chat_task(self, e_context: EventContext):
        context = e_context['context']
        # 群聊应用管理
        return self.config.get("group_app_map") and context.kwargs.get("isgroup")

    def _process_chat_task(self, e_context: EventContext):
        """
        处理LinkAI对话任务
        :param e_context: 对话上下文
        """
        context = e_context['context']
        # 群聊应用管理
        group_name = context.kwargs.get("msg").from_user_nickname
        app_code = self._fetch_group_app_code(group_name)
        if app_code:
            context.kwargs['app_code'] = app_code

    def _fetch_group_app_code(self, group_name: str) -> str:
        """
        根据群聊名称获取对应的应用code
        :param group_name: 群聊名称
        :return: 应用code
        """
        group_mapping = self.config.get("group_app_map")
        if group_mapping:
            app_code = group_mapping.get(group_name) or group_mapping.get("ALL_GROUP")
            return app_code

    def get_help_text(self, verbose=False, **kwargs):
        trigger_prefix = _get_trigger_prefix()
        help_text = "用于集成 LinkAI 提供的知识库、Midjourney绘画等能力。\n\n"
        if not verbose:
            return help_text
        help_text += f'📖 知识库\n - 群聊中指定应用: {trigger_prefix}linkai app 应用编码\n'
        help_text += f' - {trigger_prefix}linkai open: 开启对话\n'
        help_text += f' - {trigger_prefix}linkai close: 关闭对话\n'
        help_text += f'\n例如: \n"{trigger_prefix}linkai app Kv2fXJcH"\n\n'
        help_text += f"🎨 绘画\n - 生成: {trigger_prefix}mj 描述词1, 描述词2.. \n - 放大: {trigger_prefix}mju 图片ID 图片序号\n - 变换: {trigger_prefix}mjv 图片ID 图片序号\n - 重置: {trigger_prefix}mjr 图片ID"
        help_text += f"\n\n例如：\n\"{trigger_prefix}mj a little cat, white --ar 9:16\"\n\"{trigger_prefix}mju 11055927171882 2\""
        help_text += f"\n\"{trigger_prefix}mjv 11055927171882 2\"\n\"{trigger_prefix}mjr 11055927171882\""
        return help_text


# 静态方法
def _is_admin(e_context: EventContext) -> bool:
    """
    判断消息是否由管理员用户发送
    :param e_context: 消息上下文
    :return: True: 是, False: 否
    """
    context = e_context["context"]
    if context["isgroup"]:
        return context.kwargs.get("msg").actual_user_id in global_config["admin_users"]
    else:
        return context["receiver"] in global_config["admin_users"]


def _set_reply_text(content: str, e_context: EventContext, level: ReplyType = ReplyType.ERROR):
    reply = Reply(level, content)
    e_context["reply"] = reply
    e_context.action = EventAction.BREAK_PASS


def _get_trigger_prefix():
    return conf().get("plugin_trigger_prefix", "$")
