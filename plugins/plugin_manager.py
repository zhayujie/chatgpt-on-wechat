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
        self.pconf = {}

    def register(self, name: str, desc: str, version: str, author: str):
        def wrapper(plugincls):
            self.plugins[name] = plugincls
            plugincls.name = name
            plugincls.desc = desc
            plugincls.version = version
            plugincls.author = author
            plugincls.enabled = True
            logger.info("Plugin %s_v%s registered" % (name, version))
            return plugincls
        return wrapper

    def save_config(self):
        with open("plugins/plugins.json", "w", encoding="utf-8") as f:
            json.dump(self.pconf, f, indent=4, ensure_ascii=False)

    def load_config(self):
        logger.info("Loading plugins config...")

        modified = False
        if os.path.exists("plugins/plugins.json"):
            with open("plugins/plugins.json", "r", encoding="utf-8") as f:
                pconf = json.load(f)
        else:
            modified = True
            pconf = {"plugins": []}
        self.pconf = pconf
        if modified:
            self.save_config()
        return pconf

    def scan_plugins(self):
        logger.info("Scaning plugins ...")
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
        pconf = self.pconf
        new_plugins = []
        modified = False
        for name, plugincls in self.plugins.items():
            if name not in [plugin["name"] for plugin in pconf["plugins"]]:
                new_plugins.append(plugincls)
                modified = True
                logger.info("Plugin %s not found in pconfig, adding to pconfig..." % name)
                pconf["plugins"].append({"name": name, "enabled": True})
        if modified:
            self.save_config()
        return new_plugins

    def activate_plugins(self):
        for name, plugincls in self.plugins.items():
            if plugincls.enabled:
                if name not in self.instances:
                    instance = plugincls()
                    self.instances[name] = instance
                    for event in instance.handlers:
                        if event not in self.listening_plugins:
                            self.listening_plugins[event] = []
                        self.listening_plugins[event].append(name)

    def load_plugins(self):
        self.load_config()
        self.scan_plugins()
        pconf = self.pconf
        logger.debug("plugins.json config={}".format(pconf))
        for plugin in pconf["plugins"]:
            name = plugin["name"]
            enabled = plugin["enabled"]
            self.plugins[name].enabled = enabled
        self.activate_plugins()

    def emit_event(self, e_context: EventContext, *args, **kwargs):
        if e_context.event in self.listening_plugins:
            for name in self.listening_plugins[e_context.event]:
                if self.plugins[name].enabled and e_context.action == EventAction.CONTINUE:
                    logger.debug("Plugin %s triggered by event %s" % (name,e_context.event))
                    instance = self.instances[name]
                    instance.handlers[e_context.event](e_context, *args, **kwargs)
        return e_context

    def enable_plugin(self,name):
        if name not in self.plugins:
            return False
        if not self.plugins[name].enabled :
            self.plugins[name].enabled = True
            idx = next(i for i in range(len(self.pconf['plugins'])) if self.pconf["plugins"][i]['name'] == name)
            self.pconf["plugins"][idx]["enabled"] = True
            self.save_config()
            self.activate_plugins()
            return True
        return True
    
    def disable_plugin(self,name):
        if name not in self.plugins:
            return False
        if self.plugins[name].enabled :
            self.plugins[name].enabled = False
            idx = next(i for i in range(len(self.pconf['plugins'])) if self.pconf["plugins"][i]['name'] == name)
            self.pconf["plugins"][idx]["enabled"] = False
            self.save_config()
            return True
        return True
    
    def list_plugins(self):
        return self.plugins