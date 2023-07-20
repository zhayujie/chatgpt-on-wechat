import os
import json
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
        # 优先获取 plugins/config.json 中的全局配置
        plugin_conf = pconf(self.name)
        if not plugin_conf:
            # 全局配置不存在，则获取插件目录下的配置
            plugin_config_path = os.path.join(self.path, "config.json")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r") as f:
                    plugin_conf = json.load(f)
        logger.debug(f"loading plugin config, plugin_name={self.name}, conf={plugin_conf}")
        return plugin_conf

    def get_help_text(self, **kwargs):
        return "暂无帮助信息"
