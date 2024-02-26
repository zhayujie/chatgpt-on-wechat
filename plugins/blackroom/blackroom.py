# encoding:utf-8

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
import re
from config import conf, global_config

@plugins.register(
    name="blackroom",
    desire_priority=998,
    desc="Being locked in a black room",
    version="0.1",
    author="dividduang",
)
class Blackroom(Plugin):
    def __init__(self):
        super().__init__()

        self.black_list = []

        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"[cclite] 加载配置文件成功: {config}")

                self.incantation_key = config["incantation"]   
                self.amnesty_key = config["amnesty"]
                self.admin_nickname = config["admin_nickname"]

                logger.info("[blackroom] inited")
        except Exception as e:
            logger.error(f"[blackroom] init error: {e}")

        
    def on_handle_context(self, e_context: EventContext):
        context = e_context['context']
        
        msg: ChatMessage = context['msg']
        isgroup = e_context["context"].get("isgroup")
        nickname = msg.actual_user_nickname  # 获取nickname

        isadmin = False
        result = "string"
        ok = False  

        if nickname in self.black_list:
            logger.warning(f"[WX] {nickname} in In BlackRoom, ignore")
            ok, result = True, f"{self.amnesty_key[1]}"


        # 启动命令
        if self.incantation_key[0] in context.content:
            mmnick = re.findall(r'@(\S+)', context.content)
            if mmnick:
                nick = mmnick[0]
            if not isadmin and not self.is_admin_in_group(e_context["context"]):
                ok, result = True, "需要管理员权限执行"
            else:
                # 已经在black_list
                if  nickname in self.black_list or nick in self.black_list:
                    ok, result = True, self.incantation_key[1]
                else:
                    # 添加进已经在black_list
                    self.black_list.append(nick)
                    logger.warning(f"[WX] {nick} {self.incantation_key[2]}")
                    ok, result = True, f"{self.incantation_key[2]}"

        # 解除小黑屋
        elif self.amnesty_key[0] in context.content:
            mmnick = re.findall(r'@(\S+)', context.content)
            if mmnick:
                nick = mmnick[0]
            # 非管理员
            if not isadmin and not self.is_admin_in_group(e_context["context"]):
                ok, result = False, "需要管理员权限执行"
            else:
                # 不在小黑屋
                if nickname not in self.black_list and nick not in self.black_list:
                    ok, result = True, f"{self.amnesty_key[3]}"
                else:
                    self.black_list.remove(nick)
                    logger.warning(f"[WX] {nick} {self.amnesty_key[2]}")
                    ok, result = True, f"{self.amnesty_key[2]}"

        reply = Reply()
        if ok:
            reply.type = ReplyType.INFO
            reply.content = result
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
        else:
            reply.type = ReplyType.INFO
            reply.content = result
            e_context["reply"] = reply
            e_context.action = EventAction.CONTINUE  # 事件结束，并跳过处理context的默认逻辑

    def is_admin_in_group(self, context):
        if context["isgroup"]:
            return context.kwargs.get("msg").actual_user_id in global_config["admin_users"]
        return False




    def get_help_text(self, **kwargs):
        help_text = "对群主不客气会被拉到小黑屋哦！"
        return help_text
