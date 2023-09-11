# encoding:utf-8
import os
import re
import io
import json
import base64
import pickle
import requests
from PIL import Image
from plugins import *
from lib import itchat
from lib.itchat.content import *
from bridge.reply import Reply, ReplyType
from config import conf
from common.log import logger

COMMANDS = {
    "mj_help": {
        "alias": ["mj_help", "MJ帮助", "MJ文档", "MJ说明", "MJ说明文档", "mj文档", "mj说明", "mj说明文档", "mj帮助", "mjhp", "mjdoc", "mjdesc", "mjhelp"],
        "desc": "MJ帮助",
    },
    "mj_admin_cmd": {
        "alias": ["mj_admin_cmd", "MJ管理员指令"],
        "desc": "MJ管理员指令",
    },
    "mj_admin_password": {
        "alias": ["mj_admin_password", "MJ管理员认证"],
        "args": ["口令"],
        "desc": "MJ管理员认证",
    },
}


ADMIN_COMMANDS = {
    "set_mj_url": {
        "alias": ["set_mj_url", "设置MJ服务地址"],
        "args": ["服务器地址", "请求头参数", "discordapp代理地址"],
        "desc": "设置MJ服务地址",
    },
    "stop_mj": {
        "alias": ["stop_mj", "暂停MJ服务"],
        "desc": "暂停MJ服务",
    },
    "enable_mj": {
        "alias": ["enable_mj", "启用MJ服务"],
        "desc": "启用MJ服务",
    },
    "mj_tip": {
        "alias": ["mj_tip", "MJ提示"],
        "desc": "启用/关闭MJ提示",
    },
    "clean_mj": {
        "alias": ["clean_mj", "清空MJ缓存"],
        "desc": "清空MJ缓存",
    },
    "g_prefix": {
        "alias": ["g_prefix", "查询前缀"],
        "desc": "查询前缀",
    },
    "s_prefix": {
        "alias": ["s_prefix", "添加前缀"],
        "args": ["前缀类名", "前缀"],
        "desc": "添加前缀",
    },
    "r_prefix": {
        "alias": ["r_prefix", "移除前缀"],
        "args": ["前缀类名", "前缀或序列号"],
        "desc": "移除前缀",
    },
    "set_mj_admin_password": {
        "alias": ["set_mj_admin_password", "设置管理员口令"],
        "args": ["口令"],
        "desc": "修改管理员口令",
    },
    "g_admin_list": {
        "alias": ["g_admin_list", "查询管理员列表"],
        "desc": "查询管理员列表",
    },
    "s_admin_list": {
        "alias": ["s_admin_list", "添加管理员"],
        "args": ["用户ID或昵称"],
        "desc": "添加管理员",
    },
    "r_admin_list": {
        "alias": ["r_admin_list", "移除管理员"],
        "args": ["用户ID或昵称或序列号"],
        "desc": "移除管理员",
    },
    "c_admin_list": {
        "alias": ["c_admin_list", "清空管理员"],
        "desc": "清空管理员",
    },
    "s_limit": {
        "alias": ["s_limit", "设置每日作图数限制"],
        "args": ["限制值"],
        "desc": "设置每日作图数限制",
    },
    "r_limit": {
        "alias": ["r_limit", "清空重置用户作图数限制"],
        "desc": "清空重置用户作图数限制",
    },
    "g_wgroup": {
        "alias": ["g_wgroup", "查询白名单群组"],
        "desc": "查询白名单群组",
    },
    "s_wgroup": {
        "alias": ["s_wgroup", "添加白名单群组"],
        "args": ["群组名称"],
        "desc": "添加白名单群组",
    },
    "r_wgroup": {
        "alias": ["r_wgroup", "移除白名单群组"],
        "args": ["群组名称或序列号"],
        "desc": "移除白名单群组",
    },
    "c_wgroup": {
        "alias": ["c_wgroup", "清空白名单群组"],
        "desc": "清空白名单群组",
    },
    "g_wuser": {
        "alias": ["g_wuser", "查询白名单用户"],
        "desc": "查询白名单用户",
    },
    "s_wuser": {
        "alias": ["s_wuser", "添加白名单用户"],
        "args": ["用户ID或昵称"],
        "desc": "添加白名单用户",
    },
    "r_wuser": {
        "alias": ["r_wuser", "移除白名单用户"],
        "args": ["用户ID或昵称或序列号"],
        "desc": "移除白名单用户",
    },
    "c_wuser": {
        "alias": ["c_wuser", "清空白名单用户"],
        "desc": "清空白名单用户",
    },
    "g_bgroup": {
        "alias": ["g_bgroup", "查询黑名单群组"],
        "desc": "查询黑名单群组",
    },
    "s_bgroup": {
        "alias": ["s_bgroup", "添加黑名单群组"],
        "args": ["群组名称"],
        "desc": "添加黑名单群组",
    },
    "r_bgroup": {
        "alias": ["r_bgroup", "移除黑名单群组"],
        "args": ["群组名称或序列号"],
        "desc": "移除黑名单群组",
    },
    "c_bgroup": {
        "alias": ["c_bgroup", "清空黑名单群组"],
        "desc": "清空黑名单群组",
    },
    "g_buser": {
        "alias": ["g_buser", "查询黑名单用户"],
        "desc": "查询黑名单用户",
    },
    "s_buser": {
        "alias": ["s_buser", "添加黑名单用户"],
        "args": ["用户ID或昵称"],
        "desc": "添加黑名单用户",
    },
    "r_buser": {
        "alias": ["r_buser", "移除黑名单用户"],
        "args": ["用户ID或昵称或序列号"],
        "desc": "移除黑名单用户",
    },
    "c_buser": {
        "alias": ["c_buser", "清空黑名单用户"],
        "desc": "清空黑名单用户",
    },
}


def is_domain_name(string):
    pattern = r"^(?:(?:https?|ftp)://)?(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3})(?::\d+)?(?:\/[^\s]*)?(?:\/[^\s]*)?$"
    match = re.match(pattern, string)
    return match is not None


def is_ip_port_path(string):
    pattern = r"^(?:(?:https?|ftp)://)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})?(:\d+)?(/[^\s]*)?"
    match = re.match(pattern, string)
    return match is not None


def add_http_prefix(string):
    if not string.startswith("http://") and not string.startswith("https://"):
        return "http://" + string
    return string


def remove_suffix(string, suffix):
    if string.endswith(suffix):
        return string[:len(string)-len(suffix)]
    return string


def check_prefix_list(content, config):
    for key, value in config.items():
        if key.endswith("_prefix"):
            status, data = check_prefix(content, value)
            if status:
                return key, data
    return False, ""


def check_prefix(content, prefix_list):
    if not prefix_list:
        return False, ""
    for prefix in prefix_list:
        if content.startswith(prefix):
            return True, content.replace(prefix, "").strip()
    return False, ""


def image_to_base64(image_path):
    filename, extension = os.path.splitext(image_path)
    t = extension[1:]
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return f"data:image/{t};base64,{encoded_string.decode('utf-8')}"


def read_pickle(path):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def write_pickle(path, content):
    with open(path, "wb") as f:
        pickle.dump(content, f)
    return True


def read_file(path):
    with open(path, mode="r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4)
    return True


def img_to_jpeg(image_url, ddproxy = ""):
    try:
        image = io.BytesIO()
        proxy = conf().get("proxy", "")
        proxies = {}
        if proxy:
            proxies = {"http": proxy, "https": proxy}
        if ddproxy and image_url.startswith("https://cdn.discordapp.com"):
            image_url = image_url.replace("https://cdn.discordapp.com", ddproxy)
        res = requests.get(image_url, proxies=proxies, stream=True)
        idata = Image.open(io.BytesIO(res.content))
        idata = idata.convert("RGB")
        idata.save(image, format="JPEG")
        return image
    except Exception as e:
        logger.error(e)
        return False


def Text(msg, e_context: EventContext):
    return send(msg, e_context, ReplyType.TEXT)


def Image_file(msg, e_context: EventContext):
    return send(msg, e_context, ReplyType.IMAGE)


def Image_url(msg, e_context: EventContext):
    return send(msg, e_context, ReplyType.IMAGE_URL)


def Info(msg, e_context: EventContext):
    return send(msg, e_context, ReplyType.INFO)


def Error(msg, e_context: EventContext):
    return send(msg, e_context, ReplyType.ERROR)


def send(reply, e_context: EventContext, reply_type=ReplyType.TEXT, action=EventAction.BREAK_PASS):
    if isinstance(reply, Reply):
        if not reply.type and reply_type:
            reply.type = reply_type
    else:
        reply = Reply(reply_type, reply)
    e_context["reply"] = reply
    e_context.action = action
    return


def Textr(msg, e_context: EventContext):
    return send_reply(msg, e_context, ReplyType.TEXT)


def Image_filer(msg, e_context: EventContext):
    return send_reply(msg, e_context, ReplyType.IMAGE)


def Image_url_reply(msg, e_context: EventContext):
    return send_reply(msg, e_context, ReplyType.IMAGE_URL)


def Info_reply(msg, e_context: EventContext):
    return send_reply(msg, e_context, ReplyType.INFO)


def Error_reply(msg, e_context: EventContext):
    return send_reply(msg, e_context, ReplyType.ERROR)


def send_reply(reply, e_context: EventContext, reply_type=ReplyType.TEXT):
    if isinstance(reply, Reply):
        if not reply.type and reply_type:
            reply.type = reply_type
    else:
        reply = Reply(reply_type, reply)
    channel = e_context['channel']
    context = e_context['context']
    # reply的包装步骤
    rd = channel._decorate_reply(context, reply)
    # reply的发送步骤
    return channel._send_reply(context, rd)


def search_friends(name):
    userInfo = {
        "user_id": "",
        "user_nickname": ""
    }
    # 判断是id还是昵称
    if name.startswith("@"):
        friends = itchat.search_friends(userName=name)
    else:
        friends = itchat.search_friends(name=name)
    if friends and len(friends) > 0:
        if isinstance(friends, list):
            userInfo["user_id"] = friends[0]["UserName"]
            userInfo["user_nickname"] = friends[0]["NickName"]
        else:
            userInfo["user_id"] = friends["UserName"]
            userInfo["user_nickname"] = friends["NickName"]
    return userInfo


def env_detection(self, e_context: EventContext):
    trigger_prefix = conf().get("plugin_trigger_prefix", "$")
    reply = None
    # 非管理员，非白名单用户，使用次数已用完
    if not self.userInfo["isadmin"] and not self.userInfo["iswuser"] and not self.userInfo["limit"]:
        reply = Reply(ReplyType.ERROR, "[MJ] 您今日的使用次数已用完，请明日再来")
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
        return False
    if not self.config["mj_url"]:
        if self.userInfo["isadmin"]:
            reply = Reply(ReplyType.ERROR, f"未设置[mj_url]，请输入{trigger_prefix}set_mj_url+服务器地址+请求头参数进行设置。")
        else:
            reply = Reply(ReplyType.ERROR, "未设置[mj_url]，请联系管理员进行设置。")
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
        return False
    return True


def get_help_text(self, **kwargs):
    if kwargs.get("verbose") != True:
        return "这是一个AI绘画工具，只要输入想到的文字，通过人工智能产出相对应的图。"
    elif kwargs.get("admin") == True:
        help_text = f"管理员指令：\n"
        for cmd, info in ADMIN_COMMANDS.items():
            alias = [self.trigger_prefix + a for a in info["alias"][:1]]
            help_text += f"{','.join(alias)} "
            if "args" in info:
                args = [a for a in info["args"]]
                help_text += f"{' '.join(args)}"
            help_text += f": {info['desc']}\n"
        return help_text
    else:
        help_text = self.mj.help_text()
        help_text += f"\n-----------------------------\n"
        help_text += f"{self.trigger_prefix}mj_help：说明文档\n"
        is_admin = getattr(self, 'isadmin', False)
        if is_admin:
            help_text += f"{self.trigger_prefix}mj_admin_cmd：管理员指令\n"
        return help_text
