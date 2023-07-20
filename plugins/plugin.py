import os
from config import pconf
from common.log import logger

class Plugin:
    def __init__(self):
        self.handlers = {}

    def load_config(self) -> dict:
        """
        加载当前插件配置
        :return: 插件配置字典
        """
        conf = pconf(self.name)
        logger.info(f"loading from global plugin config, plugin_name={self.name}, conf={conf}")
        return conf

    def get_help_text(self, **kwargs):
        return "暂无帮助信息"
