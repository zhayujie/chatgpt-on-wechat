# encoding:utf-8

import importlib
import json
import os
from common.singleton import singleton
from .event import *
from .plugin import *
from common.log import logger


@singleton
class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.listening_plugins = {}
        self.instances = {}

    def register(self, name: str, desc: str, version: str, author: str):
        def wrapper(plugincls):
            self.plugins[name] = plugincls
            plugincls.name = name
            plugincls.desc = desc
            plugincls.version = version
            plugincls.author = author
            plugincls.enabled = True
            logger.info("Plugin %s registered" % name)
            return plugincls
        return wrapper

    def save_config(self, pconf):
        with open("plugins/plugins.json", "w", encoding="utf-8") as f:
            json.dump(pconf, f, indent=4, ensure_ascii=False)

    def load_config(self):
        logger.info("Loading plugins config...")
        plugins_dir = "plugins"
        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)
            if os.path.isdir(plugin_path):
                # 判断插件是否包含同名.py文件
                main_module_path = os.path.join(plugin_path, plugin_name+".py")
                if os.path.isfile(main_module_path):
                    # 导入插件
                    import_path = "{}.{}.{}".format(plugins_dir, plugin_name, plugin_name)
                    main_module = importlib.import_module(import_path)

        modified = False
        if os.path.exists("plugins/plugins.json"):
            with open("plugins/plugins.json", "r", encoding="utf-8") as f:
                pconf = json.load(f)
        else:
            modified = True
            pconf = {"plugins": []}
        for name, plugincls in self.plugins.items():
            if name not in [plugin["name"] for plugin in pconf["plugins"]]:
                modified = True
                logger.info("Plugin %s not found in pconfig, adding to pconfig..." % name)
                pconf["plugins"].append({"name": name, "enabled": True})
        if modified:
            self.save_config(pconf)
        return pconf

    def load_plugins(self):
        pconf = self.load_config()
        logger.debug("plugins.json config={}".format(pconf))
        for plugin in pconf["plugins"]:
            name = plugin["name"]
            enabled = plugin["enabled"]
            self.plugins[name].enabled = enabled

        for name, plugincls in self.plugins.items():
            if plugincls.enabled:
                if name not in self.instances:
                    instance = plugincls()
                    self.instances[name] = instance
                    for event in instance.handlers:
                        if event not in self.listening_plugins:
                            self.listening_plugins[event] = []
                        self.listening_plugins[event].append(name)

    def emit_event(self, e_context: EventContext, *args, **kwargs):
        if e_context.event in self.listening_plugins:
            for name in self.listening_plugins[e_context.event]:
                if e_context.action == EventAction.CONTINUE:
                    logger.debug("Plugin %s triggered by event %s" % (name,e_context.event))
                    instance = self.instances[name]
                    instance.handlers[e_context.event](e_context, *args, **kwargs)
        return e_context
