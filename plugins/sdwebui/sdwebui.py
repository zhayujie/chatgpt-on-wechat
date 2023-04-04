# encoding:utf-8

import json
import os
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import conf
import plugins
from plugins import *
from common.log import logger
import webuiapi
import io


@plugins.register(name="sdwebui", desc="利用stable-diffusion webui来画图", version="2.0", author="lanvent")
class SDWebUI(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.rules = config["rules"]
                defaults = config["defaults"]
                self.default_params = defaults["params"]
                self.default_options = defaults["options"]
                self.start_args = config["start"]
                self.api = webuiapi.WebUIApi(**self.start_args)
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[SD] inited")
        except FileNotFoundError:
            logger.warn(f"[SD] init failed, {config_path} not found, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/sdwebui .")
        except Exception as e:
            logger.warn("[SD] init failed, exception: %s, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/sdwebui ." % e)
    
    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.IMAGE_CREATE:
            return

        logger.debug("[SD] on_handle_context. content: %s" %e_context['context'].content)

        logger.info("[SD] image_query={}".format(e_context['context'].content))
        reply = Reply()
        try:
            content = e_context['context'].content[:]
            # 解析用户输入 如"横版 高清 二次元:cat"
            if ":" in content:
                keywords, prompt = content.split(":", 1)
            else:
                keywords = content
                prompt = ""

            keywords = keywords.split()

            if "help" in keywords or "帮助" in keywords:
                reply.type = ReplyType.INFO
                reply.content = self.get_help_text(verbose = True)
            else:
                rule_params = {}
                rule_options = {}
                for keyword in keywords:
                    matched = False
                    for rule in self.rules:
                        if keyword in rule["keywords"]:
                            for key in rule["params"]:
                                rule_params[key] = rule["params"][key]
                            if "options" in rule:
                                for key in rule["options"]:
                                    rule_options[key] = rule["options"][key]
                            matched = True
                            break  # 一个关键词只匹配一个规则
                    if not matched:
                        logger.warning("[SD] keyword not matched: %s" % keyword)
                
                params = {**self.default_params, **rule_params}
                options = {**self.default_options, **rule_options}
                params["prompt"] = params.get("prompt", "")+f", {prompt}"
                if len(options) > 0:
                    logger.info("[SD] cover options={}".format(options))
                    self.api.set_options(options)
                logger.info("[SD] params={}".format(params))
                result = self.api.txt2img(
                    **params
                )
                reply.type = ReplyType.IMAGE
                b_img = io.BytesIO()
                result.image.save(b_img, format="PNG")
                reply.content = b_img
            e_context.action = EventAction.BREAK_PASS  # 事件结束后，跳过处理context的默认逻辑
        except Exception as e:
            reply.type = ReplyType.ERROR
            reply.content = "[SD] "+str(e)
            logger.error("[SD] exception: %s" % e)
            e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
        finally:
            e_context['reply'] = reply

    def get_help_text(self, verbose = False, **kwargs):
        if not conf().get('image_create_prefix'):
            return "画图功能未启用"
        else:
            trigger = conf()['image_create_prefix'][0]
        help_text = "利用stable-diffusion来画图。\n"
        if not verbose:
            return help_text
        
        help_text += f"使用方法:\n使用\"{trigger}[关键词1] [关键词2]...:提示语\"的格式作画，如\"{trigger}横版 高清:cat\"\n"
        help_text += "目前可用关键词：\n"
        for rule in self.rules:
            keywords = [f"[{keyword}]" for keyword in rule['keywords']]
            help_text += f"{','.join(keywords)}"
            if "desc" in rule:
                help_text += f"-{rule['desc']}\n"
            else:
                help_text += "\n"
        return help_text