import os
from config import pconf

class Plugin:
    def __init__(self):
        self.handlers = {}

    def load_config(self) -> dict:
        """
        加载当前插件配置
        :return: 插件配置字典
        """
        return pconf(self.name)

    def get_help_text(self, **kwargs):
        return "暂无帮助信息"
