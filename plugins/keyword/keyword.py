# encoding:utf-8

import json
import os
import re

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *


@plugins.register(
    name="Keyword",
    desire_priority=900,
    hidden=True,
    desc="关键词匹配过滤",
    version="0.1",
    author="fengyege.top",
)
class Keyword(Plugin):
    def __init__(self):
        super().__init__()
        try:
            curdir = os.path.dirname(__file__)
            config_path = os.path.join(curdir, "config.json")
            conf = None
            if not os.path.exists(config_path):
                logger.debug(f"[keyword]不存在配置文件{config_path}")
                conf = {"keyword": {}}
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(conf, f, indent=4)
            else:
                logger.debug(f"[keyword]加载配置文件{config_path}")
                with open(config_path, "r", encoding="utf-8") as f:
                    conf = json.load(f)
            # 加载关键词
            self.keyword = conf["keyword"]

            logger.info("[keyword] {}".format(self.keyword))
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[keyword] inited.")
        except Exception as e:
            logger.warn(
                "[keyword] init failed, ignore or see https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins/keyword ."
            )
            raise e

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return

        content = e_context["context"].content.strip()
        logger.debug("[keyword] on_handle_context. content: %s" % content)
        # 使用正则表达式将文本分割成句子，包括中文符号和英文符号
        sentences = re.split(r'[。？！.!?;:，,~]\s*', content)
        matched_sentences = []
        for keyword, value in self.keyword.items():
            pattern = r'{}'.format(re.escape(keyword))
            for sentence in sentences:
                if re.search(pattern, sentence, re.UNICODE):
                    logger.debug(f"[keyword] 对于文本【{sentence}】, 匹配到关键字【{value}】")
                    matched_sentences.append(f"{sentence}: {value}")

        # 将匹配到的句子和值组合成一个字符串
        reply_text = "; ".join(matched_sentences)     
        if reply_text:
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = reply_text
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "关键词过滤"
        return help_text
