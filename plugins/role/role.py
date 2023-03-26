# encoding:utf-8

import json
import os
from bridge.bridge import Bridge
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common import const
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

@plugins.register(name="Role", desc="为你的Bot设置预设角色", version="1.0", author="lanvent", desire_priority= 0)
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
        sessionid = e_context['context']['session_id']
        if clist[0] == "$停止扮演":
            if sessionid in self.roleplays:
                self.roleplays[sessionid].reset()
                del self.roleplays[sessionid]
            reply = Reply(ReplyType.INFO, "角色扮演结束!")
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        elif clist[0] == "$角色":
            desckey = "descn"
        elif clist[0].lower() == "$role":
            desckey = "description"
        elif sessionid not in self.roleplays:
            return
        logger.debug("[Role] on_handle_context. content: %s" % content)
        if desckey is not None:
            if len(clist) == 1 or (len(clist) > 1 and clist[1].lower() in ["help", "帮助"]):
                reply = Reply(ReplyType.INFO, self.get_help_text())
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
                reply = Reply(ReplyType.INFO, f"角色设定为 {role} :\n"+self.roles[role][desckey])
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
        else:
            prompt = self.roleplays[sessionid].action(content)
            e_context['context'].type = ContextType.TEXT
            e_context['context'].content = prompt
            e_context.action = EventAction.BREAK

    def get_help_text(self, **kwargs):
        help_text = "输入\"$角色 {角色名}\"或\"$role {角色名}\"为我设定角色吧，\"$停止扮演 \" 可以清除设定的角色。\n\n目前可用角色列表：\n"
        for role in self.roles:
            help_text += f"[{role}]: {self.roles[role]['remark']}\n"
        return help_text
