# encoding:utf-8

import json
import os
from bridge.bridge import Bridge
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common import const
from config import conf
import plugins
from plugins import *
from common.log import logger


class RolePlay():
    def __init__(self, bot, sessionid, desc, wrapper=None):
        self.bot = bot
        self.sessionid = sessionid
        self.wrapper = wrapper or "%s"  # 用于包装用户输入
        self.desc = desc
        self.bot.sessions.build_session(self.sessionid, system_prompt=self.desc)

    def reset(self):
        self.bot.sessions.clear_session(self.sessionid)

    def action(self, user_action):
        session = self.bot.sessions.build_session(self.sessionid)
        if session.system_prompt != self.desc: # 目前没有触发session过期事件，这里先简单判断，然后重置
            session.set_system_prompt(self.desc)
        prompt = self.wrapper % user_action
        return prompt

@plugins.register(name="Role", desire_priority=0, namecn="角色扮演", desc="为你的Bot设置预设角色", version="1.0", author="lanvent")
class Role(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "roles.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.roles = {role["title"].lower(): role for role in config["roles"]}
            if len(self.roles) == 0:
                raise Exception("no role found")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            self.roleplays = {}
            logger.info("[Role] inited")
        except FileNotFoundError:
            logger.warn(f"[Role] init failed, {config_path} not found, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/role .")
        except Exception as e:
            logger.warn("[Role] init failed, exception: %s, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/role ." % e)

    def get_role(self, name, find_closest=True):
        name = name.lower()
        found_role = None
        if name in self.roles:
            found_role = name
        elif find_closest:
            import difflib

            def str_simularity(a, b):
                return difflib.SequenceMatcher(None, a, b).ratio()
            max_sim = 0.0
            max_role = None
            for role in self.roles:
                sim = str_simularity(name, role)
                if sim >= max_sim:
                    max_sim = sim
                    max_role = role
            found_role = max_role
        return found_role

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return
        bottype = Bridge().get_bot_type("chat")
        if bottype not in (const.CHATGPT, const.OPEN_AI):
            return
        bot = Bridge().get_bot("chat")
        content = e_context['context'].content[:]
        clist = e_context['context'].content.split(maxsplit=1)
        desckey = None
        customize = False
        sessionid = e_context['context']['session_id']
        trigger_prefix = conf().get('plugin_trigger_prefix', "$")
        if clist[0] == f"{trigger_prefix}停止扮演":
            if sessionid in self.roleplays:
                self.roleplays[sessionid].reset()
                del self.roleplays[sessionid]
            reply = Reply(ReplyType.INFO, "角色扮演结束!")
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        elif clist[0] == f"{trigger_prefix}角色":
            desckey = "descn"
        elif clist[0].lower() == f"{trigger_prefix}role":
            desckey = "description"
        elif clist[0] == f"{trigger_prefix}设定扮演":
            customize = True
        elif sessionid not in self.roleplays:
            return
        logger.debug("[Role] on_handle_context. content: %s" % content)
        if desckey is not None:
            if len(clist) == 1 or (len(clist) > 1 and clist[1].lower() in ["help", "帮助"]):
                reply = Reply(ReplyType.INFO, self.get_help_text(verbose=True))
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            role = self.get_role(clist[1])
            if role is None:
                reply = Reply(ReplyType.ERROR, "角色不存在")
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            else:
                self.roleplays[sessionid] = RolePlay(bot, sessionid, self.roles[role][desckey], self.roles[role].get("wrapper","%s"))
                reply = Reply(ReplyType.INFO, f"预设角色为 {role}:\n"+self.roles[role][desckey])
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
        elif customize == True:
            self.roleplays[sessionid] = RolePlay(bot, sessionid, clist[1], "%s")
            reply = Reply(ReplyType.INFO, f"角色设定为:\n{clist[1]}")
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS
        else:
            prompt = self.roleplays[sessionid].action(content)
            e_context['context'].type = ContextType.TEXT
            e_context['context'].content = prompt
            e_context.action = EventAction.BREAK

    def get_help_text(self, verbose=False, **kwargs):
        help_text = "让机器人扮演不同的角色。\n"
        if not verbose:
            return help_text
        trigger_prefix = conf().get('plugin_trigger_prefix', "$")
        help_text = f"使用方法:\n{trigger_prefix}角色"+" {预设角色名}: 设定为预设角色。\n"+f"{trigger_prefix}role"+" {预设角色名}: 同上，但使用英文设定。\n"
        help_text += f"{trigger_prefix}设定扮演"+" {角色设定}: 设定自定义角色人设。\n"
        help_text += f"{trigger_prefix}停止扮演: 清除设定的角色。\n"
        help_text += "\n目前可用的预设角色名列表: \n"
        for role in self.roles:
            help_text += f"{role}: {self.roles[role]['remark']}\n"
        help_text += f"\n命令例子: '{trigger_prefix}角色 写作助理'"
        return help_text
