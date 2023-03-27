# encoding:utf-8

import json
import os
import traceback
from typing import Tuple
from bridge.bridge import Bridge
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import load_config
import plugins
from plugins import *
from common import const
from common.log import logger

# 定义指令集
COMMANDS = {
    "help": {
        "alias": ["help", "帮助"],
        "desc": "打印指令集合",
    },
    "helpp": {
        "alias": ["helpp", "插件帮助"],
        "args": ["插件名"],
        "desc": "打印插件的帮助信息",
    },
    "auth": {
        "alias": ["auth", "认证"],
        "args": ["口令"],
        "desc": "管理员认证",
    },
    # "id": {
    #     "alias": ["id", "用户"],
    #     "desc": "获取用户id", #目前无实际意义
    # },
    "reset": {
        "alias": ["reset", "重置会话"],
        "desc": "重置会话",
    },
}

ADMIN_COMMANDS = {
    "resume": {
        "alias": ["resume", "恢复服务"],
        "desc": "恢复服务",
    },
    "stop": {
        "alias": ["stop", "暂停服务"],
        "desc": "暂停服务",
    },
    "reconf": {
        "alias": ["reconf", "重载配置"],
        "desc": "重载配置(不包含插件配置)",
    },
    "resetall": {
        "alias": ["resetall", "重置所有会话"],
        "desc": "重置所有会话",
    },
    "scanp": {
        "alias": ["scanp", "扫描插件"],
        "desc": "扫描插件目录是否有新插件",
    },
    "plist": {
        "alias": ["plist", "插件"],
        "desc": "打印当前插件列表",
    },
    "setpri": {
        "alias": ["setpri", "设置插件优先级"],
        "args": ["插件名", "优先级"],
        "desc": "设置指定插件的优先级，越大越优先",
    },
    "reloadp": {
        "alias": ["reloadp", "重载插件"],
        "args": ["插件名"],
        "desc": "重载指定插件配置",
    },
    "enablep": {
        "alias": ["enablep", "启用插件"],
        "args": ["插件名"],
        "desc": "启用指定插件",
    },
    "disablep": {
        "alias": ["disablep", "禁用插件"],
        "args": ["插件名"],
        "desc": "禁用指定插件",
    },
    "debug": {
        "alias": ["debug", "调试模式", "DEBUG"],
        "desc": "开启机器调试日志",
    },
}
# 定义帮助函数
def get_help_text(isadmin, isgroup):
    help_text = "可用指令：\n"
    for cmd, info in COMMANDS.items():
        if cmd=="auth" and (isadmin or isgroup): # 群聊不可认证
            continue

        alias=["#"+a for a in info['alias']]
        help_text += f"{','.join(alias)} "
        if 'args' in info:
            args=["{"+a+"}" for a in info['args']]
            help_text += f"{' '.join(args)} "
        help_text += f": {info['desc']}\n"
    if ADMIN_COMMANDS and isadmin:
        help_text += "\n管理员指令：\n"
        for cmd, info in ADMIN_COMMANDS.items():
            alias=["#"+a for a in info['alias']]
            help_text += f"{','.join(alias)} "
            help_text += f": {info['desc']}\n"
    return help_text

@plugins.register(name="Godcmd", desc="为你的机器人添加指令集，有用户和管理员两种角色，加载顺序请放在首位，初次运行后插件目录会生成配置文件, 填充管理员密码后即可认证", version="1.0", author="lanvent", desire_priority= 999)
class Godcmd(Plugin):

    def __init__(self):
        super().__init__()

        curdir=os.path.dirname(__file__)
        config_path=os.path.join(curdir,"config.json")
        gconf=None
        if not os.path.exists(config_path):
            gconf={"password":"","admin_users":[]}
            with open(config_path,"w") as f:
                json.dump(gconf,f,indent=4)
        else:
            with open(config_path,"r") as f:
                gconf=json.load(f)
                
        self.password = gconf["password"]
        self.admin_users = gconf["admin_users"] # 预存的管理员账号，这些账号不需要认证 TODO: 用户名每次都会变，目前不可用
        self.isrunning = True # 机器人是否运行中

        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Godcmd] inited")

    
    def on_handle_context(self, e_context: EventContext):
        context_type = e_context['context'].type
        if context_type != ContextType.TEXT:
            if not self.isrunning:
                e_context.action = EventAction.BREAK_PASS
            return
        
        content = e_context['context'].content
        logger.debug("[Godcmd] on_handle_context. content: %s" % content)
        if content.startswith("#"):
            # msg = e_context['context']['msg']
            user = e_context['context']['receiver']
            session_id = e_context['context']['session_id']
            isgroup = e_context['context']['isgroup']
            bottype = Bridge().get_bot_type("chat")
            bot = Bridge().get_bot("chat")
            # 将命令和参数分割
            command_parts = content[1:].split(" ")
            cmd = command_parts[0]
            args = command_parts[1:]
            isadmin=False
            if user in self.admin_users:
                isadmin=True
            ok=False
            result="string"
            if any(cmd in info['alias'] for info in COMMANDS.values()):
                cmd = next(c for c, info in COMMANDS.items() if cmd in info['alias'])
                if cmd == "auth":
                    ok, result = self.authenticate(user, args, isadmin, isgroup)
                elif cmd == "help":
                    ok, result = True, get_help_text(isadmin, isgroup)
                elif cmd == "helpp":
                    if len(args) != 1:
                        ok, result = False, "请提供插件名"
                    else:
                        plugins = PluginManager().list_plugins()
                        name = args[0].upper()
                        if name in plugins and plugins[name].enabled:
                            ok, result = True, PluginManager().instances[name].get_help_text(isgroup=isgroup, isadmin=isadmin)
                        else:
                            ok, result= False, "插件不存在或未启用"
                elif cmd == "id":
                    ok, result = True, f"用户id=\n{user}"
                elif cmd == "reset":
                    if bottype in (const.CHATGPT, const.OPEN_AI):
                        bot.sessions.clear_session(session_id)
                        ok, result = True, "会话已重置"
                    else:
                        ok, result = False, "当前对话机器人不支持重置会话"
                logger.debug("[Godcmd] command: %s by %s" % (cmd, user))
            elif any(cmd in info['alias'] for info in ADMIN_COMMANDS.values()):
                if isadmin:
                    if isgroup:
                        ok, result = False, "群聊不可执行管理员指令"
                    else:
                        cmd = next(c for c, info in ADMIN_COMMANDS.items() if cmd in info['alias'])
                        if cmd == "stop":
                            self.isrunning = False
                            ok, result = True, "服务已暂停"
                        elif cmd == "resume":
                            self.isrunning = True
                            ok, result = True, "服务已恢复"
                        elif cmd == "reconf":
                            load_config()
                            ok, result = True, "配置已重载"
                        elif cmd == "resetall":
                            if bottype in (const.CHATGPT, const.OPEN_AI):
                                bot.sessions.clear_all_session()
                                ok, result = True, "重置所有会话成功"
                            else:
                                ok, result = False, "当前对话机器人不支持重置会话"
                        elif cmd == "debug":
                            logger.setLevel('DEBUG')
                            ok, result = True, "DEBUG模式已开启"
                        elif cmd == "plist":
                            plugins = PluginManager().list_plugins()
                            ok = True
                            result = "插件列表：\n"
                            for name,plugincls in plugins.items():
                                result += f"{plugincls.name}_v{plugincls.version} {plugincls.priority} - "
                                if plugincls.enabled:
                                    result += "已启用\n"
                                else:
                                    result += "未启用\n"
                        elif cmd == "scanp":
                            new_plugins = PluginManager().scan_plugins()
                            ok, result = True, "插件扫描完成"
                            PluginManager().activate_plugins()
                            if len(new_plugins) >0 :
                                result += "\n发现新插件：\n"
                                result += "\n".join([f"{p.name}_v{p.version}" for p in new_plugins])
                            else :
                                result +=", 未发现新插件"
                        elif cmd == "setpri":
                            if len(args) != 2:
                                ok, result = False, "请提供插件名和优先级"
                            else:
                                ok = PluginManager().set_plugin_priority(args[0], int(args[1]))
                                if ok:
                                    result = "插件" + args[0] + "优先级已设置为" + args[1]
                                else:
                                    result = "插件不存在"
                        elif cmd == "reloadp":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok = PluginManager().reload_plugin(args[0])
                                if ok:
                                    result = "插件配置已重载"
                                else:
                                    result = "插件不存在"
                        elif cmd == "enablep":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok = PluginManager().enable_plugin(args[0])
                                if ok:
                                    result = "插件已启用"
                                else:
                                    result = "插件不存在"
                        elif cmd == "disablep":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok = PluginManager().disable_plugin(args[0])
                                if ok:
                                    result = "插件已禁用"
                                else:
                                    result = "插件不存在"

                        logger.debug("[Godcmd] admin command: %s by %s" % (cmd, user))
                else:
                    ok, result = False, "需要管理员权限才能执行该指令"
            else:
                ok, result = False, f"未知指令：{cmd}\n查看指令列表请输入#help \n"
            
            reply = Reply()
            if ok:
                reply.type = ReplyType.INFO
            else:
                reply.type = ReplyType.ERROR
            reply.content = result
            e_context['reply'] = reply

            e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑
        elif not self.isrunning:
            e_context.action = EventAction.BREAK_PASS
    
    def authenticate(self, userid, args, isadmin, isgroup) -> Tuple[bool,str] : 
        if isgroup:
            return False,"请勿在群聊中认证"
        
        if isadmin:
            return False,"管理员账号无需认证"
        
        if len(self.password) == 0:
            return False,"未设置口令，无法认证"
        
        if len(args) != 1:
            return False,"请提供口令"
        
        password = args[0]
        if password == self.password:
            self.admin_users.append(userid)
            return True,"认证成功"
        else:
            return False,"认证失败"

    def get_help_text(self, isadmin = False, isgroup = False, **kwargs):
        return get_help_text(isadmin, isgroup)