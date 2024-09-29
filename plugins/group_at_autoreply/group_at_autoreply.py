import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *


@plugins.register(
    name="GroupAtAutoreply",
    desire_priority=0,
    hidden=True,
    enabled=True,
    desc="群聊中出现@某人时，触发某人的自动回复",
    version="0.1",
    author="zexin.li",
)
class GroupAtAutoreply(Plugin):

    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            if self.config is None:
                self.config = {}
                config_path = os.path.join(os.path.dirname(__file__), "config.json")
                with open(config_path, "w") as f:
                    json.dump(self.config, f, indent=4)
            logger.info("[GroupAtAutoreply] inited")
            self.handlers[Event.ON_RECEIVE_MESSAGE] = self.on_receive_message
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[GroupAtAutoreply]初始化异常：{e}")
            raise "[GroupAtAutoreply] init failed, ignore "

    def _update_config(self, username, enabled, reply_text):
        new_config = {
            "enabled": enabled,
            "reply_text": reply_text if reply_text else ""
        }
        self.config[username] = new_config
        self.save_config(self.config)

    # 收到消息的时候，直接判断是否需要自动回复，需要的话，直接准备好，放在 context
    def on_receive_message(self, e_context: EventContext):
        if self.config is None:
            return

        context = e_context["context"]
        if context.type != ContextType.TEXT:
            return

        if context.get("isgroup", False):
            # 群聊消息，检测是否触发了自动回复
            autoreply_members = []
            if isinstance(context["msg"].at_list, list):
                for at in context["msg"].at_list:
                    if at in self.config:
                        at_config = self.config[at]
                        if at_config["enabled"]:
                            autoreply_members.append(at)

            if len(autoreply_members) > 0:
                context["autoreply_members"] = autoreply_members
                e_context.action = EventAction.BREAK_PASS
        elif str(context.content).startswith("$群自动回复"):
            # 私聊消息，且是设置自动回复的
            lines = str(context.content).split("\n")[1:]
            enabled = None  # 开关
            reply_text = None  # 回复内容

            for line in lines:
                line = line.strip()
                kwarg = line.split(":")
                if len(kwarg) <= 1:
                    kwarg = line.split("：")
                    if len(kwarg) <= 1:
                        continue
                key = kwarg[0].strip()
                value = kwarg[1].strip()
                if key == "开关":
                    enabled = True if "打开" == value else (False if "关闭" == value else None)
                elif key == "回复内容":
                    reply_text = value

            help_info = "指令错误，参考示例如下：\n\n$群自动回复\n开关: 打开\n回复内容: 请稍后联系~\n\n$群自动回复\n开关: 关闭"
            if enabled is None:
                autoreply_config_result = help_info
            elif enabled and reply_text is None:
                autoreply_config_result = help_info
            else:
                cmsg = context["msg"]
                username = cmsg.from_user_nickname
                self._update_config(username, enabled, reply_text)
                autoreply_config_result = f"群自动回复，已{'开启' if enabled else '关闭'}"

            context["autoreply_config_result"] = autoreply_config_result
            e_context.action = EventAction.BREAK_PASS

    def on_handle_context(self, e_context: EventContext):
        context = e_context["context"]
        reply_text = None
        if "autoreply_members" in context:
            autoreply_members = context["autoreply_members"]
            if autoreply_members is None or len(autoreply_members) == 0:
                return

            reply_text = ""
            for member in autoreply_members:
                member_config = self.config[member]
                if member_config["enabled"]:
                    reply_text += f"\n{member}自动回复：{member_config['reply_text']}"
        elif "autoreply_config_result" in context:
            reply_text = context["autoreply_config_result"]

        if reply_text is not None:
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = reply_text
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
