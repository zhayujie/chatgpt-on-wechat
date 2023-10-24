# encoding:utf-8
import requests

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType

from plugins import *


@plugins.register(
    name="Kxt",
    desire_priority=777,
    hidden=True,
    desc="跨信通网络服务插件",
    version="0.2",
    author="wzy",
)
class Kxt(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Kxt] 初始化完成")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT
        ]:
            return

        content = e_context["context"].content
        cmd_list = content.split()
        logger.info("[kxt] 接收到内容. content: %s" % content)
        logger.info("[kxt] 接收到参数. cmd_list: %s" % cmd_list)
        if cmd_list[0].lower() == f"$kxt":
            result_msg = "未知错误"
            if cmd_list[1] == f"查询税号有效性":
                codes = cmd_list[2:]
                response = requests.post(url="https://testapi_saas.kuaxintong.com/vat/system/verify/checkTaxCodeNoLogin2",
                                        json=codes,
                                        timeout=(5, 40))
                data = response.json()

                if data["code"] == 200:
                    result_msg = "查询结果如下:\n"
                    dataArr = data["data"] or []
                    for key, value in dataArr.items():
                        result_msg += f"{key} - "
                        result_msg += f"{value}"
                        result_msg += "\n"
                else:
                    result_msg = f"异常:{data['msg']}"
            else:
                result_msg = "未知命令"

            reply = Reply()
            reply.type = ReplyType.TEXT

            if e_context["context"]["isgroup"]:
                reply.content = result_msg
            else:
                reply.content = result_msg
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
            return
        else:
            e_context.action = EventAction.CONTINUE
            return

    def get_help_text(self, **kwargs):
        help_text = (
            "$kxt 查询税号有效性\n"
            "说明: 税号一行一个,最多不超过30个\n"
            "示例：\n$kxt 查询税号有效性 \n"
            "FR78899507503\n"
            "DE78899507502\n"
            "\n"
        )
        return help_text
