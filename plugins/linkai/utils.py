from config import global_config
from bridge.reply import Reply, ReplyType
from plugins.event import EventContext, EventAction


class Util:
    @staticmethod
    def is_admin(e_context: EventContext) -> bool:
        """
        判断消息是否由管理员用户发送
        :param e_context: 消息上下文
        :return: True: 是, False: 否
        """
        context = e_context["context"]
        if context["isgroup"]:
            actual_user_id = context.kwargs.get("msg").actual_user_id
            for admin_user in global_config["admin_users"]:
                if actual_user_id and actual_user_id in admin_user:
                    return True
            return False
        else:
            return context["receiver"] in global_config["admin_users"]

    @staticmethod
    def set_reply_text(content: str, e_context: EventContext, level: ReplyType = ReplyType.ERROR):
        reply = Reply(level, content)
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
