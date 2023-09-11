# encoding:utf-8
import os
import time
import json
import plugins
from bridge.context import ContextType
from bridge.reply import ReplyType
from common.log import logger
from common.expired_dict import ExpiredDict
from plugins import *
from channel.chat_message import ChatMessage
from typing import Tuple
from config import conf
from lib import itchat
from lib.itchat.content import *
from .mjapi import _mjApi
from .mjcache import _imgCache
from .ctext import *


@plugins.register(
    name="MidJourney",
    namecn="MJ绘画",
    desc="一款AI绘画工具",
    version="1.0.46",
    author="mouxan"
)
class MidJourney(Plugin):
    def __init__(self):
        super().__init__()

        gconf = {
            "mj_url": "",
            "mj_api_secret": "",
            "mj_tip": True,
            "mj_admin_password": "",
            "discordapp_proxy": "",
            "daily_limit": 3,
            "imagine_prefix": [
                "/i",
                "/mj"
            ],
            "fetch_prefix": [
                "/f"
            ],
            "up_prefix": [
                "/u"
            ],
            "pad_prefix": [
                "/p"
            ],
            "blend_prefix": [
                "/b"
            ],
            "describe_prefix": [
                "/d"
            ],
            "queue_prefix": [
                "/q"
            ],
            "end_prefix": [
                "/e"
            ],
            "reroll_prefix": [
                "/r"
            ],
        }

        # 读取和写入配置文件
        curdir = os.path.dirname(__file__)
        self.json_path = os.path.join(curdir, "config.json")
        self.roll_path = os.path.join(curdir, "user_info.pkl")
        self.user_datas_path = os.path.join(curdir, "user_datas.pkl")
        tm_path = os.path.join(curdir, "config.json.template")

        env = {}
        for key in gconf.keys():
            if os.environ.get(key, None):
                env[key] = os.environ.get(key)
                break

        jld = {}
        if os.path.exists(self.json_path):
            # 读取config.json配置文件
            jld = json.loads(read_file(self.json_path))
        elif os.path.exists(tm_path):
            # 读取config.json.template配置文件
            jld = json.loads(read_file(tm_path))

        gconf = {**gconf, **jld, **env}
        if is_domain_name(gconf["mj_url"]) or is_ip_port_path(gconf["mj_url"]):
            gconf["mj_url"] = add_http_prefix(gconf["mj_url"])
            gconf["mj_url"] = remove_suffix(gconf["mj_url"], "/mj")
        else:
            logger.info("[MJ] 请配置合法域名")
            gconf["mj_url"] = ""

        if gconf["discordapp_proxy"]:
            if is_domain_name(gconf["discordapp_proxy"]) or is_ip_port_path(gconf["discordapp_proxy"]):
                gconf["discordapp_proxy"] = add_http_prefix(gconf["discordapp_proxy"])
            else:
                logger.info("[MJ] 请配置合法代理地址")
                gconf["discordapp_proxy"] = ""

        if gconf["mj_admin_password"] == "":
            self.temp_password = "123456"
            logger.info("[MJ] 因未设置管理员密码，本次的临时密码为%s。" % self.temp_password)
        else:
            self.temp_password = None

        # 读取和写入配置文件
        for key, value in gconf.items():
            if key.endswith("_prefix"):
                gconf[key] = eval(value) if isinstance(value, str) else value

        self.config = gconf

        logger.info("[MJ] config={}".format(self.config))

        # 重新写入配置文件
        write_file(self.json_path, self.config)

        self.roll = {
            "mj_admin_users": [],
            "mj_groups": [],
            "mj_users": [],
            "mj_bgroups": [],
            "mj_busers": []
        }
        if os.path.exists(self.roll_path):
            sroll = read_pickle(self.roll_path)
            self.roll = {**self.roll, **sroll}
        # 写入用户列表
        write_pickle(self.roll_path, self.roll)

        self.user_datas = {}
        if os.path.exists(self.user_datas_path):
            self.user_datas = read_pickle(self.user_datas_path)

        # 目前没有设计session过期事件，这里先暂时使用过期字典
        if conf().get("expires_in_seconds"):
            self.sessions = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            self.sessions = dict()

        self.ismj = True  # 机器人是否运行中

        self.mj = _mjApi(self.config)

        self.trigger_prefix = conf().get("plugin_trigger_prefix", "$")

        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context

        logger.info("[MJ] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT,
            ContextType.IMAGE,
        ]:
            return

        context = e_context['context']
        content = context.content
        msg: ChatMessage = context["msg"]
        self.sessionid = context["session_id"]
        self.userInfo = self.get_user_info(e_context)
        self.isgroup = self.userInfo["isgroup"]

        self.mj.set_user(json.dumps(self.userInfo))

        if ContextType.TEXT == context.type and content.startswith(self.trigger_prefix):
            return self.handle_command(e_context)

        # 拦截非白名单黑名单群组
        if not self.userInfo["isadmin"] and self.isgroup and not self.userInfo["iswgroup"] and self.userInfo["isbgroup"]:
            return

        # 拦截黑名单用户
        if not self.userInfo["isadmin"] and self.userInfo["isbuser"]:
            return

        # 判断是否在运行中
        if not self.ismj:
            return

        # 图片
        if context.type == ContextType.IMAGE:
            # 需要调用准备函数下载图片，否则会出错
            msg.prepare()
            return self.handle_image(e_context)

        # 文字
        if context.type == ContextType.TEXT:
            # 判断是否是指令
            return self.handle_text(e_context)

    get_help_text = lambda self, **kwargs: get_help_text(self, **kwargs)

    def handle_text(self, e_context: EventContext):
        context = e_context['context']
        content = context.content
        if not context or not content:
            return
        # 判断指令渠道
        pn, prompt  = check_prefix_list(content, self.config)
        if pn:
            # 环境检测
            env = env_detection(self, e_context)
            if not env:
                return
        if pn == "imagine_prefix":
            if not prompt:
                return Info("[MJ] 请输入要绘制的描述文字", e_context)
            if self.sessionid in self.sessions:
                self.sessions[self.sessionid].reset()
                del self.sessions[self.sessionid]
            return self.imagine(prompt, [], e_context)
        elif pn == "up_prefix":
            if not prompt:
                return Info("[MJ] 请输入任务ID", e_context)
            if self.sessionid in self.sessions:
                self.sessions[self.sessionid].reset()
                del self.sessions[self.sessionid]
            return self.up(prompt, e_context)
        elif pn == "pad_prefix":
            if not prompt:
                return Info("[MJ] 请输入要绘制的描述文字进行开启垫图模式，然后发送一张或者多张图片", e_context)
            self.sessions[self.sessionid] = _imgCache(self.sessionid, "imagine", prompt)
            return Text(f"✨ 垫图模式\n✏ 请再发送一张或者多张图片", e_context)
        elif pn == "blend_prefix":
            self.sessions[self.sessionid] = _imgCache(self.sessionid, "blend", prompt)
            return Text(f"✨ 混图模式\n✏ 请发送两张或多张图片，然后输入['{self.config['end_prefix'][0]}']结束", e_context)
        elif pn == "describe_prefix":
            self.sessions[self.sessionid] = _imgCache(self.sessionid, "describe", prompt)
            return Text(f"✨ 识图模式\n✏ 请发送一张图片", e_context)
        elif pn == "end_prefix":
            # 从会话中获取缓存的图片
            img_cache = None
            if self.sessionid in self.sessions:
                img_cache = self.sessions[self.sessionid].get_cache()
            if not img_cache:
                return Error("[MJ] 请先输入指令开启绘图模式", e_context)
            base64Array = img_cache["base64Array"]
            prompt = img_cache["prompt"]
            instruct = img_cache["instruct"]
            length = len(base64Array)
            if instruct == 'imagine' and length < 1:
                return Text(f"✨ 垫图模式\n✏ 请发送一张或多张图片方可完成垫图", e_context)
            elif instruct == 'imagine' and length >= 1:
                if self.sessionid in self.sessions:
                    self.sessions[self.sessionid].reset()
                    del self.sessions[self.sessionid]
                return self.imagine(prompt, base64Array, e_context)
            if instruct == "blend" and length >= 2:
                if self.sessionid in self.sessions:
                    self.sessions[self.sessionid].reset()
                    del self.sessions[self.sessionid]
                return self.blend(base64Array, prompt, e_context)
            else:
                return Text(f"✨ 混图模式\n✏ 请再发送一张图片方可完成混图", e_context)
        elif pn == "fetch_prefix":
            logger.debug("[MJ] /fetch id={}".format(prompt))
            status, msg, imageUrl = self.mj.fetch(prompt)
            rt = ReplyType.TEXT
            rc = msg
            if not status:
                rt = ReplyType.ERROR
            if status and imageUrl:
                if self.config["mj_tip"]:
                    send_reply(msg, e_context)
                    rt = ReplyType.IMAGE
                    rc = img_to_jpeg(imageUrl, self.config["discordapp_proxy"])
                    if not rc:
                        rt = ReplyType.ERROR
                        rc = "图片下载发送失败"
            if self.sessionid in self.sessions:
                self.sessions[self.sessionid].reset()
                del self.sessions[self.sessionid]
            return send(rc, e_context, rt)
        elif pn == "queue_prefix":
            status, msg = self.mj.task_queue()
            rc = msg
            rt = ReplyType.TEXT if status else ReplyType.ERROR
            if self.sessionid in self.sessions:
                self.sessions[self.sessionid].reset()
                del self.sessions[self.sessionid]
            return send(rc, e_context, rt)
        elif pn == "reroll_prefix":
            if not prompt:
                return Info("[MJ] 请输入任务ID", e_context)
            if self.sessionid in self.sessions:
                self.sessions[self.sessionid].reset()
                del self.sessions[self.sessionid]
            return self.reroll(prompt, e_context)

    # 识图
    def handle_image(self, e_context: EventContext):
        # 获取图片base64
        context = e_context['context']
        if not context or not context.content:
            return
        base64 = image_to_base64(context.content)

        # 从会话中获取缓存的图片
        img_cache = None
        if self.sessionid in self.sessions:
            img_cache = self.sessions[self.sessionid].get_cache()

        # 识图模式
        if (not self.isgroup and not img_cache) or (not self.isgroup and not img_cache["instruct"]) or (img_cache and img_cache["instruct"] == "describe"):
            # 环境检测
            env = env_detection(self, e_context)
            if not env:
                return
            if self.sessionid in self.sessions:
                self.sessions[self.sessionid].reset()
                del self.sessions[self.sessionid]
            return self.describe(base64, e_context)

        # 垫图模式和混图模式
        if img_cache and (img_cache["instruct"] == "imagine" or img_cache["instruct"] == "blend"):
            # 环境检测
            env = env_detection(self, e_context)
            if not env:
                return
            names = '垫图' if img_cache['instruct'] == 'imagine' else '混图'
            if self.sessionid not in self.sessions:
                return Info(f"[MJ] 请先输入指令开启{names}模式", e_context)
            self.sessions[self.sessionid].action(base64)
            img_cache = self.sessions[self.sessionid].get_cache()
            length = len(img_cache["base64Array"])
            if img_cache['instruct'] == 'blend' and length < 2:
                return Text(f"✏  请再发送一张或多张图片", e_context)
            else:
                return Text(f"✏  您已发送{length}张图片，可以发送更多图片或者发送['{self.config['end_prefix'][0]}']开始{names}操作", e_context)

    # 指令处理
    def handle_command(self, e_context: EventContext):
        content = e_context['context'].content
        com = content[1:].strip().split()
        cmd = com[0]
        args = com[1:]
        if any(cmd in info["alias"] for info in COMMANDS.values()):
            cmd = next(c for c, info in COMMANDS.items() if cmd in info["alias"])
            if cmd == "mj_help":
                return Info(get_help_text(self, verbose=True), e_context)
            elif cmd == "mj_admin_cmd":
                if not self.userInfo["isadmin"]:
                    return Error("[MJ] 您没有权限执行该操作，请先进行管理员认证", e_context)
                return Info(get_help_text(self, verbose=True, isadmin=True), e_context)
            elif cmd == "mj_admin_password":
                ok, result = self.authenticate(self.userInfo, args)
                if not ok:
                    return Error(result, e_context)
                else:
                    return Info(result, e_context)
        elif any(cmd in info["alias"] for info in ADMIN_COMMANDS.values()):
            cmd = next(c for c, info in ADMIN_COMMANDS.items() if cmd in info["alias"])
            if not self.userInfo["isadmin"]:
                return Error("[MJ] 您没有权限执行该操作，请先进行管理员认证", e_context)
            if cmd == "mj_tip":
                self.config["mj_tip"] = not self.config["mj_tip"]
                write_file(self.json_path, self.config)
                return Info(f"[MJ] 提示功能已{'开启' if self.config['mj_tip'] else '关闭'}", e_context)
            elif cmd == "s_limit":
                if len(args) < 1:
                    return Error("[MJ] 请输入需要设置的数量", e_context)
                limit = int(args[0])
                if limit < 0:
                    return Error("[MJ] 数量不能小于0", e_context)
                self.config["daily_limit"] = limit
                for index, item in self.user_datas.items():
                    self.user_datas[index]["limit"] = limit
                write_pickle(self.user_datas_path, self.user_datas)
                write_file(self.json_path, self.config)
                return Info(f"[MJ] 每日使用次数已设置为{limit}次", e_context)
            elif cmd == "r_limit":
                for index, item in self.user_datas.items():
                    self.user_datas[index]["limit"] = self.config["daily_limit"]
                write_pickle(self.user_datas_path, self.user_datas)
                return Info(f"[MJ] 所有用户每日使用次数已重置为{self.config['daily_limit']}次", e_context)
            elif cmd == "set_mj_admin_password":
                if len(args) < 1:
                    return Error("[MJ] 请输入需要设置的密码", e_context)
                password = args[0]
                if self.isgroup:
                    return Error("[MJ] 为避免密码泄露，请勿在群聊中进行修改", e_context)
                if len(password) < 6:
                    return Error("[MJ] 密码长度不能小于6位", e_context)
                if password == self.temp_password:
                    return Error("[MJ] 不能使用临时密码，请重新设置", e_context)
                if password == self.config['mj_admin_password']:
                    return Error("[MJ] 新密码不能与旧密码相同", e_context)
                self.config["mj_admin_password"] = password
                write_file(self.json_path, self.config)
                return Info("[MJ] 管理员口令设置成功", e_context)
            elif cmd == "stop_mj":
                self.ismj = False
                return Info("[MJ] 服务已暂停", e_context)
            elif cmd == "enable_mj":
                self.ismj = True
                return Info("[MJ] 服务已启用", e_context)
            elif cmd == "clean_mj":
                if self.sessionid in self.sessions:
                    self.sessions[self.sessionid].reset()
                    del self.sessions[self.sessionid]
                return Info("[MJ] 会话已清理", e_context)
            elif cmd =="g_prefix":
                text = "[MJ] 前缀列表：\n"
                for key, value in self.config.items():
                    if key.endswith("_prefix"):
                        text += f"{key}：[{'，'.join(f'{data}' for data in value)}]\n"
                return Info(text, e_context)
            elif cmd == "s_prefix":
                if not args or len(args) < 1 or len(args) < 2:
                    return Error("[MJ] 请输入需要前缀类名和所需要添加的前缀，例如[$s_prefix imagine_prefix /mj]", e_context)
                prefix_name = args[0]
                data = args[1]
                if prefix_name not in self.config:
                    return Error(f"[MJ] 类名[{prefix_name}]不存在", e_context)
                prefix_list = self.config[prefix_name]
                if data in prefix_list:
                    return Error(f"[MJ] 前缀[{data}]已存在", e_context)
                if data.startswith("[") and data.endswith("]"):
                    prefix_list = data
                else:
                    prefix_list.append(data)
                self.config[prefix_name] = prefix_list
                write_file(self.json_path, self.config)
                text = f"[MJ] 前缀[{data}]已添加到[{prefix_name}]列表中"
                t = "\n"
                text += t.join(f'{index+1}. {data}' for index, data in enumerate(prefix_list))
                return Info(text, e_context)
            elif cmd == "r_prefix":
                if not args or len(args) < 1 or len(args) < 2:
                    return Error("[MJ] 请输入需要前缀类名和所需要删除的前缀或序列号，例如[$r_prefix imagine_prefix /mj]", e_context)
                prefix_name = args[0]
                data = args[1]
                if prefix_name not in self.config:
                    return Error(f"[MJ] 类名[{prefix_name}]不存在", e_context)
                if len(self.config[prefix_name]) == 0:
                    return Error(f"[MJ] 类名[{prefix_name}]列表为空", e_context)
                if len(self.config[prefix_name]) == 1:
                    return Error(f"[MJ] 类名[{prefix_name}]列表中只有一个元素，无法删除", e_context)
                prefix_list = self.config[prefix_name]
                prefix_names = ""
                if data.isdigit():
                    index = int(data) - 1
                    if index < 0 or index >= len(prefix_list):
                        return Error(f"[MJ] 序列号[{data}]不存在", e_context)
                    prefix_names = prefix_list[index]
                    del prefix_list[index]
                else:
                    if data not in prefix_list:
                        return Error(f"[MJ] 前缀[{data}]不存在", e_context)
                    prefix_names = data
                    prefix_list.remove(data)
                self.config[prefix_name] = prefix_list
                write_file(self.json_path, self.config)
                text = f"[MJ] 前缀[{prefix_names}]已从[{prefix_name}]列表中移除"
                t = "\n"
                text += t.join(f'{index+1}. {data}' for index, data in enumerate(prefix_list))
                return Info(text, e_context)
            elif cmd == "g_admin_list" and not self.isgroup:
                adminUser = self.roll["mj_admin_users"]
                t = "\n"
                nameList = t.join(f'{index+1}. {data["user_nickname"]}' for index, data in enumerate(adminUser))
                return Info(f"[MJ] 管理员用户\n{nameList}", e_context)
            elif cmd == "c_admin_list" and not self.isgroup:
                self.roll["mj_admin_users"] = []
                write_pickle(self.roll_path, self.roll)
                return Info("[MJ] 管理员用户已清空", e_context)
            elif cmd == "s_admin_list" and not self.isgroup:
                user_name = args[0] if args and args[0] else ""
                adminUsers = self.roll["mj_admin_users"]
                buser = self.roll["mj_busers"]
                if not args or len(args) < 1:
                    return Error("[MJ] 请输入需要设置的管理员名称或ID", e_context)
                index = -1
                for i, user in enumerate(adminUsers):
                    if user["user_id"] == user_name or user["user_nickname"] == user_name:
                        index = i
                        break
                if index >= 0:
                    return Error(f"[MJ] 管理员[{adminUsers[index]['user_nickname']}]已在列表中", e_context)
                for i, user in enumerate(buser):
                    if user == user_name:
                        index = i
                        break
                if index >= 0:
                    return Error(f"[MJ] 用户[{user_name}]已在黑名单中，如需添加请先进行移除", e_context)
                userInfo = {
                    "user_id": user_name,
                    "user_nickname": user_name
                }
                # 判断是否是itchat平台
                if conf().get("channel_type", "wx") == "wx":
                    userInfo = search_friends(user_name)
                    # 判断user_name是否在列表中
                    if not userInfo or not userInfo["user_id"]:
                        return Error(f"[MJ] 用户[{user_name}]不存在通讯录中", e_context)
                adminUsers.append(userInfo)
                self.roll["mj_admin_users"] = adminUsers
                # 写入用户列表
                write_pickle(self.roll_path, self.roll)
                return Info(f"[MJ] 管理员[{userInfo['user_nickname']}]已添加到列表中", e_context)
            elif cmd == "r_admin_list" and not self.isgroup:
                text = ""
                adminUsers = self.roll["mj_admin_users"]
                if len(args) < 1:
                    return Error("[MJ] 请输入需要移除的管理员名称或ID或序列号", e_context)
                if args and args[0]:
                    if args[0].isdigit():
                        index = int(args[0]) - 1
                        if index < 0 or index >= len(adminUsers):
                            return Error(f"[MJ] 序列号[{args[0]}]不存在", e_context)
                        user_name = adminUsers[index]['user_nickname']
                        del adminUsers[index]
                        self.roll["mj_admin_users"] = adminUsers
                        write_pickle(self.roll_path, self.roll)
                        text = f"[MJ] 管理员[{user_name}]已从列表中移除"
                    else:
                        user_name = args[0]
                        index = -1
                        for i, user in enumerate(adminUsers):
                            if user["user_nickname"] == user_name or user["user_id"] == user_name:
                                index = i
                                break
                        if index >= 0:
                            del adminUsers[index]
                            text = f"[MJ] 管理员[{user_name}]已从列表中移除"
                            self.roll["mj_admin_users"] = adminUsers
                            write_pickle(self.roll_path, self.roll)
                        else:
                            return Error(f"[MJ] 管理员[{user_name}]不在列表中", e_context)
                return Info(text, e_context)
            elif cmd == "g_wgroup" and not self.isgroup:
                text = ""
                groups = self.roll["mj_groups"]
                if len(groups) == 0:
                    text = "[MJ] 白名单群组：无"
                else:
                    t = "\n"
                    nameList = t.join(f'{index+1}. {group}' for index, group in enumerate(groups))
                    text = f"[MJ] 白名单群组\n{nameList}"
                return Info(text, e_context)
            elif cmd == "c_wgroup":
                self.roll["mj_groups"] = []
                write_pickle(self.roll_path, self.roll)
                return Info("[MJ] 群组白名单已清空", e_context)
            elif cmd == "s_wgroup":
                groups = self.roll["mj_groups"]
                bgroups = self.roll["mj_bgroups"]
                if not self.isgroup and len(args) < 1:
                    return Error("[MJ] 请输入需要设置的群组名称", e_context)
                if self.isgroup:
                    group_name = self.userInfo["group_name"]
                if args and args[0]:
                    group_name = args[0]
                if group_name in groups:
                    return Error(f"[MJ] 群组[{group_name}]已在白名单中", e_context)
                if group_name in bgroups:
                    return Error(f"[MJ] 群组[{group_name}]已在黑名单中，如需添加请先进行移除", e_context)
                # 判断是否是itchat平台，并判断group_name是否在列表中
                if conf().get("channel_type", "wx") == "wx":
                    chatrooms = itchat.search_chatrooms(name=group_name)
                    if len(chatrooms) == 0:
                        return Error(f"[MJ] 群组[{group_name}]不存在", e_context)
                groups.append(group_name)
                self.roll["mj_groups"] = groups
                write_pickle(self.roll_path, self.roll)
                return Info(f"[MJ] 群组[{group_name}]已添加到白名单", e_context)
            elif cmd == "r_wgroup":
                groups = self.roll["mj_groups"]
                if not self.isgroup and len(args) < 1:
                    return Error("[MJ] 请输入需要移除的群组名称或序列号", e_context)
                if self.isgroup:
                    group_name = self.userInfo["group_name"]
                if args and args[0]:
                    if args[0].isdigit():
                        index = int(args[0]) - 1
                        if index < 0 or index >= len(groups):
                            return Error(f"[MJ] 序列号[{args[0]}]不在白名单中", e_context)
                        group_name = groups[index]
                    else:
                        group_name = args[0]
                if group_name in groups:
                    groups.remove(group_name)
                    self.roll["mj_groups"] = groups
                    write_pickle(self.roll_path, self.roll)
                    return Info(f"[MJ] 群组[{group_name}]已从白名单中移除", e_context)
                else:
                    return Error(f"[MJ] 群组[{group_name}]不在白名单中", e_context)
            elif cmd == "g_bgroup" and not self.isgroup:
                text = ""
                bgroups = self.roll["mj_bgroups"]
                if len(bgroups) == 0:
                    text = "[MJ] 黑名单群组：无"
                else:
                    t = "\n"
                    nameList = t.join(f'{index+1}. {group}' for index, group in enumerate(bgroups))
                    text = f"[MJ] 黑名单群组\n{nameList}"
                return Info(text, e_context)
            elif cmd == "c_bgroup":
                self.roll["mj_bgroups"] = []
                write_pickle(self.roll_path, self.roll)
                return Info("[MJ] 已清空黑名单群组", e_context)
            elif cmd == "s_bgroup":
                groups = self.roll["mj_groups"]
                bgroups = self.roll["mj_bgroups"]
                if not self.isgroup and len(args) < 1:
                    return Error("[MJ] 请输入需要设置的群组名称", e_context)
                if self.isgroup:
                    group_name = self.userInfo["group_name"]
                if args and args[0]:
                    group_name = args[0]
                if group_name in groups:
                    return Error(f"[MJ] 群组[{group_name}]已在白名单中，如需添加请先进行移除", e_context)
                if group_name in bgroups:
                    return Error(f"[MJ] 群组[{group_name}]已在黑名单中", e_context)
                # 判断是否是itchat平台，并判断group_name是否在列表中
                if conf().get("channel_type", "wx") == "wx":
                    chatrooms = itchat.search_chatrooms(name=group_name)
                    if len(chatrooms) == 0:
                        return Error(f"[MJ] 群组[{group_name}]不存在", e_context)
                bgroups.append(group_name)
                self.roll["mj_bgroups"] = bgroups
                write_pickle(self.roll_path, self.roll)
                return Info(f"[MJ] 群组[{group_name}]已添加到黑名单", e_context)
            elif cmd == "r_bgroup":
                bgroups = self.roll["mj_bgroups"]
                if not self.isgroup and len(args) < 1:
                    return Error("[MJ] 请输入需要移除的群组名称或序列号", e_context)
                if self.isgroup:
                    group_name = self.userInfo["group_name"]
                if args and args[0]:
                    if args[0].isdigit():
                        index = int(args[0]) - 1
                        if index < 0 or index >= len(bgroups):
                            return Error(f"[MJ] 序列号[{args[0]}]不在黑名单中", e_context)
                        group_name = bgroups[index]
                    else:
                        group_name = args[0]
                if group_name in bgroups:
                    bgroups.remove(group_name)
                    self.roll["mj_bgroups"] = bgroups
                    write_pickle(self.roll_path, self.roll)
                    return Info(f"[MJ] 群组[{group_name}]已从黑名单中移除", e_context)
                else:
                    return Error(f"[MJ] 群组[{group_name}]不在黑名单中", e_context)
            elif cmd == "g_buser" and not self.isgroup:
                busers = self.roll["mj_busers"]
                if len(busers) == 0:
                    return Info("[MJ] 黑名单用户：无", e_context)
                else:
                    t = "\n"
                    nameList = t.join(f'{index+1}. {data}' for index, data in enumerate(busers))
                    return Info(f"[MJ] 黑名单用户\n{nameList}", e_context)
            elif cmd == "g_wuser" and not self.isgroup:
                users = self.roll["mj_users"]
                if len(users) == 0:
                    return Info("[MJ] 白名单用户：无", e_context)
                else:
                    t = "\n"
                    nameList = t.join(f'{index+1}. {data}' for index, data in enumerate(users))
                    return Info(f"[MJ] 白名单用户\n{nameList}", e_context)
            elif cmd == "c_wuser":
                self.roll["mj_users"] = []
                write_pickle(self.roll_path, self.roll)
                return Info("[MJ] 用户白名单已清空", e_context)
            elif cmd == "c_buser":
                self.roll["mj_busers"] = []
                write_pickle(self.roll_path, self.roll)
                return Info("[MJ] 用户黑名单已清空", e_context)
            elif cmd == "s_wuser":
                user_name = args[0] if args and args[0] else ""
                users = self.roll["mj_users"]
                busers = self.roll["mj_busers"]
                if not args or len(args) < 1:
                    return Error("[MJ] 请输入需要设置的用户名称或ID", e_context)
                index = -1
                for i, user in enumerate(users):
                    if user == user_name:
                        index = i
                        break
                if index >= 0:
                    return Error(f"[MJ] 用户[{user_name}]已在白名单中", e_context)
                for i, user in enumerate(busers):
                    if user == user_name:
                        index = i
                        break
                if index >= 0:
                    return Error(f"[MJ] 用户[{user_name}]已在黑名单中，如需添加请先移除黑名单", e_context)
                # 判断是否是itchat平台
                if conf().get("channel_type", "wx") == "wx":
                    userInfo = search_friends(user_name)
                    # 判断user_name是否在列表中
                    if not userInfo or not userInfo["user_id"]:
                        return Error(f"[MJ] 用户[{user_name}]不存在通讯录中", e_context)
                users.append(user_name)
                self.roll["mj_users"] = users
                write_pickle(self.roll_path, self.roll)
                return Info(f"[MJ] 用户[{user_name}]已添加到白名单", e_context)
            elif cmd == "s_buser":
                user_name = args[0] if args and args[0] else ""
                users = self.roll["mj_users"]
                busers = self.roll["mj_busers"]
                if not args or len(args) < 1:
                    return Error("[MJ] 请输入需要设置的用户名称或ID", e_context)
                index = -1
                for i, user in enumerate(users):
                    if user == user_name:
                        index = i
                        break
                if index >= 0:
                    return Error(f"[MJ] 用户[{user_name}]已在白名单中，如需添加请先移除白名单", e_context)
                for i, user in enumerate(busers):
                    if user == user_name:
                        index = i
                        break
                if index >= 0:
                    return Error(f"[MJ] 用户[{user_name}]已在黑名单中", e_context)
                # 判断是否是itchat平台
                if conf().get("channel_type", "wx") == "wx":
                    userInfo = search_friends(user_name)
                    # 判断user_name是否在列表中
                    if not userInfo or not userInfo["user_id"]:
                        return Error(f"[MJ] 用户[{user_name}]不存在通讯录中", e_context)
                busers.append(user_name)
                self.roll["mj_busers"] = busers
                write_pickle(self.roll_path, self.roll)
                return Info(f"[MJ] 用户[{user_name}]已添加到黑名单", e_context)
            elif cmd == "r_wuser":
                text = ""
                users = self.roll["mj_users"]
                if len(args) < 1:
                    return Error("[MJ] 请输入需要移除的用户名称或ID或序列号", e_context)
                if args and args[0]:
                    if args[0].isdigit():
                        index = int(args[0]) - 1
                        if index < 0 or index >= len(users):
                            return Error(f"[MJ] 序列号[{args[0]}]不存在", e_context)
                        user_name = users[index]
                        del users[index]
                        self.roll["mj_users"] = users
                        write_pickle(self.roll_path, self.roll)
                        text = f"[MJ] 用户[{user_name}]已从白名单中移除"
                    else:
                        user_name = args[0]
                        index = -1
                        for i, user in enumerate(users):
                            if user == user_name:
                                index = i
                                break
                        if index >= 0:
                            del users[index]
                            text = f"[MJ] 用户[{user_name}]已从白名单中移除"
                            self.roll["mj_users"] = users
                            write_pickle(self.roll_path, self.roll)
                        else:
                            return Error(f"[MJ] 用户[{user_name}]不在白名单中", e_context)
                return Info(text, e_context)
            elif cmd == "r_buser":
                text = ""
                busers = self.roll["mj_busers"]
                if len(args) < 1:
                    return Error("[MJ] 请输入需要移除的用户名称或ID或序列号", e_context)
                if args and args[0]:
                    if args[0].isdigit():
                        index = int(args[0]) - 1
                        if index < 0 or index >= len(busers):
                            return Error(f"[MJ] 序列号[{args[0]}]不存在", e_context)
                        user_name = busers[index]
                        del busers[index]
                        self.roll["mj_busers"] = busers
                        write_pickle(self.roll_path, self.roll)
                        text = f"[MJ] 用户[{user_name}]已从黑名单中移除"
                    else:
                        user_name = args[0]
                        index = -1
                        for i, user in enumerate(busers):
                            if user == user_name:
                                index = i
                                break
                        if index >= 0:
                            del busers[index]
                            text = f"[MJ] 用户[{user_name}]已从黑名单中移除"
                            self.roll["mj_busers"] = busers
                            write_pickle(self.roll_path, self.roll)
                        else:
                            return Error(f"[MJ] 用户[{user_name}]不在黑名单中", e_context)
                return Info(text, e_context)
            else:
                if len(args) < 1:
                    return Error("[MJ] 请输入需要设置的服务器地址", e_context)
                mj_url = args[0] if args[0] else ""
                mj_api_secret = args[1] if len(args) == 2 else ""
                proxy = args[2] if len(args) == 3 else ""
                if is_domain_name(mj_url) or is_ip_port_path(mj_url):
                    mj_url = add_http_prefix(mj_url)
                    mj_url = remove_suffix(mj_url, "/mj")
                else:
                    return Error("[MJ] 请输入正确的服务器地址", e_context)
                if proxy:
                    if is_domain_name(proxy) or is_ip_port_path(proxy):
                        proxy = add_http_prefix(proxy)
                    else:
                        return Error("[MJ] 请输入正确的代理地址", e_context)
                self.config["mj_url"] = mj_url
                self.config["mj_api_secret"] = mj_api_secret
                self.config["discordapp_proxy"] = proxy
                self.mj.set_mj(mj_url, mj_api_secret, proxy)
                write_file(self.json_path, self.config)
                return Info("MJ服务设置成功\nmj_url={}\nmj_api_secret={}\ndiscordapp_proxy={}".format(mj_url, mj_api_secret, proxy), e_context)

    def authenticate(self, userInfo, args) -> Tuple[bool, str]:
        isgroup = userInfo["isgroup"]
        isadmin = userInfo["isadmin"]
        if isgroup:
            return False, "[MJ] 为避免密码泄露，请勿在群聊中认证"

        if isadmin:
            return False, "[MJ] 管理员账号无需认证"

        if len(args) != 1:
            return False, "[MJ] 请输入密码"

        password = args[0]
        if password == self.config['mj_admin_password'] or password == self.temp_password:
            self.roll["mj_admin_users"].append({
                "user_id": userInfo["user_id"],
                "user_nickname": userInfo["user_nickname"]
            })
            write_pickle(self.roll_path, self.roll)
            return True, f"[MJ] 认证成功 {'，请尽快设置口令' if password == self.temp_password else ''}"
        else:
            return False, "[MJ] 认证失败"

    def imagine(self, prompt, base64Array, e_context: EventContext):
        logger.info("[MJ] /imagine prompt={} imgList={}".format(prompt, base64Array))
        status, msg, id = self.mj.imagine(prompt, base64Array)
        return self._reply(status, msg, id, e_context)

    def up(self, id, e_context: EventContext):
        logger.debug("[MJ] /up id={}".format(id))
        status, msg, id = self.mj.simpleChange(id)
        return self._reply(status, msg, id, e_context)

    def describe(self, base64, e_context: EventContext):
        logger.debug("[MJ] /describe img={}".format(base64))
        status, msg, id = self.mj.describe(base64)
        return self._reply(status, msg, id, e_context, "text" if not self.config['mj_tip'] else "image")

    def blend(self, base64Array, dimensions, e_context: EventContext):
        logger.debug("[MJ] /blend imgList={} dimensions={}".format(base64Array, dimensions))
        status, msg, id = self.mj.blend(base64Array, dimensions)
        return self._reply(status, msg, id, e_context)

    def get_user_info(self, e_context: EventContext):
        # 获取当前时间戳
        current_timestamp = time.time()
        # 将当前时间戳和给定时间戳转换为日期字符串
        current_date = time.strftime("%Y-%m-%d", time.localtime(current_timestamp))
        groups = self.roll["mj_groups"]
        bgroups = self.roll["mj_bgroups"]
        users = self.roll["mj_users"]
        busers = self.roll["mj_busers"]
        mj_admin_users = self.roll["mj_admin_users"]
        context = e_context['context']
        msg: ChatMessage = context["msg"]
        isgroup = context.get("isgroup", False)
        # 写入用户信息，企业微信没有from_user_nickname，所以使用from_user_id代替
        uid = msg.from_user_id if not isgroup else msg.actual_user_id
        uname = (msg.from_user_nickname if msg.from_user_nickname else uid) if not isgroup else msg.actual_user_nickname
        userInfo = {
            "user_id": uid,
            "user_nickname": uname,
            "isgroup": isgroup,
            "group_id": msg.from_user_id if isgroup else "",
            "group_name": msg.from_user_nickname if isgroup else "",
        }
        logger.info("[MJ] user_datas={}".format(self.user_datas))
        # 判断是否是新的一天
        if uid not in self.user_datas or "mj_data" not in self.user_datas[uid] or "mj_data" not in self.user_datas[uid] or self.user_datas[uid]["mj_data"]["time"] != current_date:
            mj_data = {
                "limit": self.config["daily_limit"],
                "time": current_date
            }
            if uid in self.user_datas and self.user_datas[uid]["mj_data"]:
                self.user_datas[uid]["mj_data"] = mj_data
            else:
                self.user_datas[uid] = {
                    "mj_data": mj_data
                }
            write_pickle(self.user_datas_path, self.user_datas)
        limit = self.user_datas[uid]["mj_data"]["limit"] if "mj_data" in self.user_datas[uid] and "limit" in self.user_datas[uid]["mj_data"] and self.user_datas[uid]["mj_data"]["limit"] and self.user_datas[uid]["mj_data"]["limit"] > 0 else False
        userInfo['limit'] = limit
        userInfo['isadmin'] = uid in [user["user_id"] for user in mj_admin_users]
        userInfo['iswuser'] = uname in [user["user_nickname"] for user in users]
        userInfo['isbuser'] = uname in [user["user_nickname"] for user in busers]
        userInfo['iswgroup'] = userInfo["group_name"] in groups
        userInfo['isbgroup'] = userInfo["group_name"] in bgroups
        return userInfo

    def reroll(self, id, e_context: EventContext):
        logger.debug("[MJ] /reroll id={}".format(id))
        status, msg, id = self.mj.reroll(id)
        return self._reply(status, msg, id, e_context)

    def _reply(self, status, msg, id, e_context: EventContext, reply_type="image"):
        userInfo = self.get_user_info(e_context)
        if status:
            if self.config["mj_tip"]:
                send_reply(msg, e_context)
            self.user_datas[userInfo['user_id']]["mj_data"]["limit"] -= 1
            write_pickle(self.user_datas_path, self.user_datas)
            rc, rt = self.get_f_img(id, e_context, reply_type)
            return send(rc, e_context, rt)
        else:
            return Error(msg, e_context)

    def get_f_img(self, id, e_context: EventContext, reply_type="image"):
        status, msg, imageUrl = self.mj.get_f_img(id)
        rt = ReplyType.TEXT
        rc = msg
        if not status:
            rt = ReplyType.ERROR
        if status and imageUrl:
            if self.config["mj_tip"] or reply_type == "image":
                if self.config["mj_tip"]:
                    send_reply(msg, e_context)
                rt = ReplyType.IMAGE
                rc = img_to_jpeg(imageUrl, self.config["discordapp_proxy"])
        if not rc:
            rt = ReplyType.ERROR
            rc = "图片下载发送失败"
        return rc, rt
