# encoding:utf-8
import json
import os
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import conf
import plugins
from plugins import *
from common.log import logger
import replicate

@plugins.register(name="replicate", desc="利用replicate api来画图", version="0.1", author="lanvent")
class SDWebUI(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        if not os.path.exists(config_path):
            logger.info('[RP] 配置文件不存在，将使用config-template.json模板')
            config_path = os.path.join(curdir, "config.json.template")
        try:
            self.apitoken = None
            if os.environ.get("replicate_api_token", None):
                self.apitoken = os.environ.get("replicate_api_token")
            if os.environ.get("replicate_api_token".upper(), None):
                self.apitoken = os.environ.get("replicate_api_token".upper())

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.rules = config["rules"]
                self.default_params = config["defaults"]
                if not self.apitoken:
                    self.apitoken = config["replicate_api_token"]
                if self.apitoken == "YOUR API TOKEN":
                    raise Exception("please set your api token in config or environment variable.")
                self.client = replicate.Client(self.apitoken)
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[RP] inited")
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.warn(f"[RP] init failed, config.json not found.")
            else:
                logger.warn("[RP] init failed.")
            raise e
    
    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.IMAGE_CREATE:
            return

        logger.debug("[RP] on_handle_context. content: %s" %e_context['context'].content)

        logger.info("[RP] image_query={}".format(e_context['context'].content))
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
                for keyword in keywords:
                    matched = False
                    for rule in self.rules:
                        if keyword in rule["keywords"]:
                            for key in rule["params"]:
                                rule_params[key] = rule["params"][key]
                            matched = True
                            break  # 一个关键词只匹配一个规则
                    if not matched:
                        logger.warning("[RP] keyword not matched: %s" % keyword)
                
                params = {**self.default_params, **rule_params}
                params["prompt"] = params.get("prompt", "")+f", {prompt}"
                logger.info("[RP] params={}".format(params))
                model = self.client.models.get(params.pop("model"))
                version = model.versions.get(params.pop("version"))
                result = version.predict(**params)
                reply.type = ReplyType.IMAGE_URL
                reply.content = result[0]
            e_context.action = EventAction.BREAK_PASS  # 事件结束后，跳过处理context的默认逻辑
        except Exception as e:
            reply.type = ReplyType.ERROR
            reply.content = "[RP] "+str(e)
            logger.error("[RP] exception: %s" % e)
            e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
        finally:
            e_context['reply'] = reply

    def get_help_text(self, verbose = False, **kwargs):
        if not conf().get('image_create_prefix'):
            return "画图功能未启用"
        else:
            trigger = conf()['image_create_prefix'][0]
        help_text = "利用replicate api来画图。\n"
        if not verbose:
            return help_text
        
        help_text += f"使用方法:\n使用\"{trigger}[关键词1] [关键词2]...:提示语\"的格式作画，如\"{trigger}竖版:girl\"\n"
        help_text += "目前可用关键词：\n"
        for rule in self.rules:
            keywords = [f"[{keyword}]" for keyword in rule['keywords']]
            help_text += f"{','.join(keywords)}"
            if "desc" in rule:
                help_text += f"-{rule['desc']}\n"
            else:
                help_text += "\n"
        return help_text

