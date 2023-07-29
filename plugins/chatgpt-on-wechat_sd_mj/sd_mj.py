# encoding:utf-8

# 导入所需的模块和类
import io
import json
import os
import time
import threading
import requests
import base64

import webuiapi
from bridge.bridge import Bridge
import plugins
from bridge.context import *
from bridge.reply import Reply, ReplyType
from common import const
from common.log import logger
from common.expired_dict import ExpiredDict
from config import conf
from PIL import Image
from plugins import *

# 定义一个名为StableDiffusion_prompt的类，用于处理用户输入的内容并生成stable-diffusion需要的输入
class StableDiffusion_prompt:
    def __init__(self, bot, sessionid, gpt_set_prompt):
        # 初始化实例变量
        self.bot = bot
        self.sessionid = sessionid
        bot.sessions.clear_session(sessionid)
        self.first_interact = True
        self.gpt_set_prompt = gpt_set_prompt

        # 重置实例状态

    def reset(self):
        self.bot.sessions.clear_session(self.sessionid)
        self.first_interact = True

        # 处理用户输入的内容并生成stable-diffusion需要的输入

    def action(self, context: Context) -> Context:
        if context.type == ContextType.IMAGE: #如果传入的是图像，则使用上一次生成的prompt
            return
        if self.first_interact:
            pre_gpt_prompt = self.gpt_set_prompt + context.content # 如果是第一次进入画图模式则将预先设置chatgpt设定为预设的角色
            self.first_interact = False
        else:
            pre_gpt_prompt = context.content
        gpt_reply = self.bot.reply(pre_gpt_prompt, context) # 将输入的内容传入chatgpt，让他生成prompt
        context.content = gpt_reply.content

class Ai_darw:
    def __init__(self):
        pass
    def draw(self, context: Context):
        pass

class MidJourney(Ai_darw):
    def __init__(self, base_url, module):
        self.base_url = base_url
        self.pre_prompt = ""
        self.work = False
        self.process = 0
        self.img = None
        self.id = None
        self.module = module
        
    def draw(self, context: Context):
        if self.work:
            respone = self.method_respone("FETCH")
            if respone.json()['status'] == 'FAILURE':
                reply = Reply(ReplyType.ERROR, "生成失败，请重试。失败原因：" + respone.json()['failReason'])
            elif respone.json()['status'] == 'SUCCESS':
                res_img = requests.get(respone.json()['imageUrl']).content
                self.img = io.BytesIO(res_img)
                reply = Reply(ReplyType.IMAGE, self.img)
            elif respone.json()['status'] == 'IN_PROGRESS':
                reply = Reply(ReplyType.INFO, f"图像正在生成目前进度为{respone.json()['progress']}，请稍等一下")
                return reply
            else:
                reply = Reply(ReplyType.ERROR, "未知错误")
            return reply
        else:
            self.work = True

            if context.type == ContextType.TEXT: 
                logger.info("[MJ] recive text: " + context.content)
                self.pre_prompt = context.content
                data_body = {**self.module.get("IMAGINE")["body"], **{"prompt": self.pre_prompt}}
                respone = self.method_respone("IMAGINE", **data_body)
                if respone.status_code == 200:
                    self.id = respone.json()['result']
                    reply = Reply(ReplyType.INFO, "开始生成图像！本次prompt:" + self.pre_prompt + "，本次ID："+ self.id + ",生成一般需要等待30s，请等待一段时间后回复任意消息获得结果")
                else:
                    reply = Reply(ReplyType.ERROR, "生成失败，请重试。失败原因：" + respone.json()['failReason'])
            elif context.type == ContextType.IMAGE:
                with open(context.content, "rb") as f:
                    img = base64.b64encode(f.read()).decode()
                data_body = {**self.module.get("IMAGINE")["body"], **{"prompt": self.pre_prompt, "base64":"data:image/png;base64," + img}}
                respone = self.method_respone("IMAGINE", **data_body)
                if respone.status_code == 200:
                    self.id = respone.json()['result']
                    reply = Reply(ReplyType.INFO, "开始生成图像！本次prompt:" + self.pre_prompt + "，本次ID："+ self.id + ",生成一般需要等待30s，请等待一段时间后回复任意消息获得结果")
                else:
                    reply = Reply(ReplyType.ERROR, "生成失败，请重试。失败原因：" + respone.json()['failReason'])
            return reply

    def method_respone(self, op_name, **kwargs):
        if op_name == "FETCH":
            return requests.request("GET", self.base_url + self.module.get(op_name)["path"] + self.id + "/fetch")
        elif op_name in self.module:
            new_kwargs = {**self.module.get(op_name)["body"], **kwargs}
            return requests.request("POST", self.base_url + self.module.get(op_name)["path"], json=new_kwargs)

class StableDiffusion(Ai_darw):
    def __init__(self, user_id):
        user_config_dir = os.path.join(os.path.dirname(__file__), "user_config")
        user_config_path = os.path.join(user_config_dir, f"config_{user_id}.json")
        defalut_config_path = os.path.join(user_config_dir, "sd_default.json")
        try:
            # 尝试从用户配置文件中读取配置信息
            with open(user_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

        except FileNotFoundError:
            # 如果用户配置文件不存在，则从默认配置文件中读取配置信息，并将其写入用户配置文件中
            with open(defalut_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            with open(user_config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

        except Exception as e:
            logger.warn("[SD] init failed, ignore or see")
            raise e
        
        self.usr_config = config
        self.user_config_path = user_config_path
        self.params = config["params"]
        self.options = config["options"]
        self.start_args = config["start"]
        self.api = webuiapi.WebUIApi(**self.start_args)
        self.pre_prompt = self.options["lora"] + ", " + self.params["prompt"]
        self.process = 0
        self.work = False
        self.img = None
        self.img_fix = False

        # 将输入发送给stable-diffusion webui并返回生成的图像
    def config(self, options):
        pass

    def draw(self, context: Context):
        self.process = self.api.get_progress()['progress']
        if self.process != 0 and not self.work:
            reply = Reply(ReplyType.INFO, "目前队列中有任务生成，请稍后再试")
        elif self.work and self.process != 0:
            reply = Reply(ReplyType.INFO, f"图像正在生成目前进度为{self.process * 100:.1f}%，请稍等一下")
        elif self.work and self.process == 0:
            if self.img:
                reply = Reply(ReplyType.IMAGE, self.img)
            else:
                reply = Reply(ReplyType.ERROR, "完了找不到图片了，请重试")
            self.work = False
        else:
            self.work = True
            work_thread = threading.Thread(target=self.draw_async, args=(context,))
            work_thread.start()
            if context.type == ContextType.TEXT:
                reply = Reply(ReplyType.INFO, "开始生成图像！本次prompt:" + context.content + "，sd生成一般需要等待30s") 
            elif context.type == ContextType.IMAGE and self.img_fix:
                reply = Reply(ReplyType.INFO, "开始修复图像！需要等待30s左右。放大倍率为2倍，使用ESRGAN_4x算法")
            else:
                reply = Reply(ReplyType.INFO, "开始生成图像！本次prompt:" + self.pre_prompt + "，并且使用了ControlNet，生成一般需要等待30s")
        return reply

    def draw_async(self, context: Context):
        self.api.util_set_model(self.options["model"])
        params = self.params.copy()
        params["prompt"] = self.options["lora"] + ", " + self.params["prompt"]
        if context.type == ContextType.TEXT: #如果这次传入的是文字，则用Chatgpt生成的prompt
            params["prompt"] += context["content"]
            logger.info(
                "[SD] image_query={}".format(params["prompt"])
            )
            result = self.api.txt2img(**params)
            self.pre_prompt = params["prompt"]
        elif context.type == ContextType.IMAGE: #如果这次传入的是图像，则用上次生成的prompt
            params["prompt"] = self.pre_prompt
            with Image.open(context.content) as f: #将从微信保存的图片打开,content为图片路径/tmp/pictureid.png
                img = f.copy()
            if self.img_fix: #如果是修复模式就不需要进行调用txt2img来生成图片
                result = self.api.extra_single_image(image=img,
                                 upscaler_1=webuiapi.Upscaler.ESRGAN_4x,
                                 upscaling_resize=2.0)
            else: #因为传入的是图片，使用ControlNet来进行图生图
                unit1 = webuiapi.ControlNetUnit(
                    input_image=img,
                    module=self.options["controlnet_mod"],
                    model=self.options["controlnet_model"],
                )
                logger.info(
                    "[SD] image_query={}".format(params["prompt"])
                )

                result = self.api.txt2img(**params, controlnet_units=[unit1]) #相关api可以在webuiapi的github仓库中查看
        self.img = io.BytesIO() #将传回的结果存在内存中，不作为文件保存在电脑上，节省io操作，并且免得清理文件
        result.image.save(self.img, format="PNG") 


# 定义一个名为SD_MJ的类，用于处理来自聊天机器人的事件
@plugins.register(
    name="sd", namecn= "mj", desc="利用StableDiffusion或者MidJourney来画图", version="1.1", author="steins"
)
class SD_MJ(Plugin):
    def __init__(self):
        # 初始化实例变量
        super().__init__()
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        default_conf_path = os.path.join(curdir, "config.json.template")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.error("[SD] config.json not found! use default config")
                with open(default_conf_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            else:
                logger.error("[SD] init failed, ignore or see")
            raise e
        self.config = config
        self.tasks = {}
        self.gpt_set_prompt = config["gpt_prompt"]
        self.commands = config["commands"]
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.trigger_prefix = conf().get("plugin_trigger_prefix", "$")
        logger.info("[SD] inited")
        if conf().get("expires_in_seconds"):
            self.prompt_session = ExpiredDict(conf().get("expires_in_seconds"))
            self.instance = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            self.prompt_session = dict()
            self.instance = dict()
    # 事件处理程序，用于处理来自聊天机器人的上下文
    def on_handle_context(self, e_context: EventContext):
        # 获取事件上下文中的内容和会话ID
        channel = e_context["channel"]
        bottype = Bridge().get_bot_type("chat")
        if bottype not in [const.OPEN_AI, const.CHATGPT, const.CHATGPTONAZURE]:
            return
        if ReplyType.IMAGE in channel.NOT_SUPPORT_REPLYTYPE:
            return
        bot = Bridge().get_bot("chat")            
        context = e_context["context"]
        sessionid = context["session_id"]
        content = context.content
        content_type = context.type
        trigger_prefix = self.trigger_prefix

        if content_type == ContextType.IMAGE:
            cmsg = context["msg"]
            cmsg.prepare()
        if content_type == ContextType.TEXT:
            clist = content.split(maxsplit=1)
            if clist[0] == f"{trigger_prefix}sd":
                if len(clist) == 1:
                    reply = self.sd_help(sessionid, bot)
                elif clist[1] in self.commands:
                    command_handler = getattr(self, f"sd_{clist[1]}")
                    reply = command_handler(sessionid, bot)
                elif clist[1] in self.config.get("sd_keywords", []):
                    reply = self.sd_setconfig(sessionid, clist[1])
                else:
                    reply = self.sd_help(sessionid, bot)
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                    return
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            elif clist[0] == f"{trigger_prefix}mj":
                if len(clist) == 1:
                    reply = self.mj_help(sessionid, bot)
                elif clist[1] in self.commands:
                    command_handler = getattr(self, f"mj_{clist[1]}")
                    reply = command_handler(sessionid, bot)
                else:
                    reply = self.mj_help(sessionid, bot)
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS

                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
                    
        if sessionid in self.prompt_session:
            logger.debug(
                "[SD] on_handle_context. content: %s"
                % context.content
            )
            # 如果当前有正在进行的画图，则将用户输入的内容传递给相应的实例进行处理，并将结果传递给StableDiffusion_draw实例进行图像生成
            self.prompt_session[sessionid].action(context)
            reply = self.instance[sessionid].draw(context)
            # 将生成的图像作为回复发送给聊天机器人
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

    def get_help_text(self, verbose = False, **kwargs):
        help_text = f"利用stable-diffusion或者MidJourney来画图。(关键词:sd,mj)\n"
        if not verbose:
            return help_text
        trigger = conf().get("plugin_trigger_prefix", "$") 
        help_text += f'使用方法:\n使用"{trigger}sd start"进入sd画图模式，或者{trigger}mj start进入mj画图模式。\n \
然后跟他对话或者发送图片即可让他画图"\n然后使用"{trigger}sd 关键词"可以更改模型和其他参数\n'
        help_text += "目前可用关键词：\n"
        rule = self.config["sd_keywords"]
        for keyword, details in rule.items():
            desc = details.get("desc", "")
            help_text += f"{keyword}：{desc}\n"
        return help_text
    def sd_start(self, sessionid, bot):
        if sessionid not in self.prompt_session:
            reply = Reply(
            ReplyType.INFO,
            f"开始画图！请发送图片或文字。该程序是先输入文字描述然后在输入图片进行精修若直接输入图片则使用默认描述。输入{self.trigger_prefix}sd stop停止画图。")   
        else:
            reply = Reply(ReplyType.INFO, "检测到已经进入画图模式，已重置")
        
        self.prompt_session[sessionid] = StableDiffusion_prompt(bot, sessionid, self.gpt_set_prompt)
        self.instance[sessionid] = StableDiffusion(sessionid)
        return reply
    def sd_stop(self, sessionid, bot): 
        if sessionid in self.prompt_session:                                                                          
            # 如果当前有正在进行的画图，则删除相应的实例并发送回复
            self.prompt_session[sessionid].reset()
            with open(self.instance[sessionid].user_config_path, "w") as f:
                json.dump(self.instance[sessionid].usr_config, f, indent=4, ensure_ascii=False)
            del self.prompt_session[sessionid]
            del self.instance[sessionid]
            reply = Reply(ReplyType.INFO, "停止画图！")
        else:
            # 如果当前没有正在进行的画图，则发送回复
            reply = Reply(ReplyType.INFO, "当前没有正在进行的画图！")
        return reply
    def sd_config(self, sessionid, bot):
        non_instance = False
        if not self.instance.get(sessionid):
            self.instance[sessionid] = StableDiffusion(sessionid)
            non_instance = True
        usr_params = self.instance[sessionid].params
        usr_options= self.instance[sessionid].options
        reply = Reply(ReplyType.INFO, f"当前配置为：{usr_params},{usr_options}")
        if non_instance:
            del self.instance[sessionid]
        return reply
    def sd_setconfig(self, sessionid, command): 
        non_instance = False
        if not self.instance.get(sessionid):
            self.instance[sessionid] = StableDiffusion(sessionid)
            non_instance = True
        add_prams = self.config["sd_keywords"][command]["params"]
        add_options = self.config["sd_keywords"][command]["options"]
        new_params = {**self.instance[sessionid].params, **add_prams}
        new_options= {**self.instance[sessionid].options, **add_options}
        self.instance[sessionid].usr_config["params"] = new_params
        self.instance[sessionid].params = new_params
        self.instance[sessionid].usr_config["options"] = new_options
        self.instance[sessionid].options = new_options
        with open(self.instance[sessionid].user_config_path, "w") as f:
            json.dump(self.instance[sessionid].usr_config, f, indent=4, ensure_ascii=False)
        reply = Reply(ReplyType.INFO, f"已设置参数{add_options},{add_prams}！")
        if non_instance:
            del self.instance[sessionid]
        return reply

    def sd_help(self, sessionid, bot):
        reply = Reply(ReplyType.INFO, self.get_help_text(verbose=True))
        return reply
    def sd_fix(self, sessionid, bot):
        if sessionid not in self.prompt_session:
            reply = Reply(ReplyType.INFO, "当前没有正在进行的画图！")
        else:
            reply = Reply(ReplyType.INFO, "开始修图模式！请发送图片。输入{self.trigger_prefix}sd fstop停止修图。")
            self.instance[sessionid].img_fix = True
        return reply
    def sd_fstop(self, sessionid, bot):
        if sessionid not in self.prompt_session:
            reply = Reply(ReplyType.INFO, "当前没有正在进行的画图！")
        else:
            reply = Reply(ReplyType.INFO, "停止修图模式！")
            self.instance[sessionid].img_fix = False
        return reply
    
    def mj_start(self, sessionid, bot):
        if sessionid not in self.prompt_session:
            reply = Reply(
            ReplyType.INFO,
            f"开始画图！请发送图片或文字。该程序是先输入文字描述然后在输入图片进行精修若直接输入图片则使用默认描述。输入{self.trigger_prefix}mj stop停止画图。")   
        else:
            reply = Reply(ReplyType.INFO, "检测到已经进入画图模式，已重置")
        
        self.prompt_session[sessionid] = StableDiffusion_prompt(bot, sessionid, self.gpt_set_prompt)
        self.instance[sessionid] = MidJourney(base_url= self.config["base_url"],module=self.config["mj_keywords"])
        return reply
    def mj_stop(self, sessionid, bot): 
        if sessionid in self.prompt_session:                                                                          
            # 如果当前有正在进行的画图，则删除相应的实例并发送回复
            self.prompt_session[sessionid].reset()
            del self.prompt_session[sessionid]
            del self.instance[sessionid]
            reply = Reply(ReplyType.INFO, "停止画图！")
        else:
            # 如果当前没有正在进行的画图，则发送回复
            reply = Reply(ReplyType.INFO, "当前没有正在进行的画图！")
        return reply
   
    def mj_help(self, sessionid, bot):
        reply = Reply(ReplyType.INFO, self.get_help_text(verbose=True))
        return reply