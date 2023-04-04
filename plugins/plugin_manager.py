# encoding:utf-8

import importlib
import json
import os
from common.singleton import singleton
from common.sorted_dict import SortedDict
from .event import *
from common.log import logger
from config import conf


@singleton
class PluginManager:
    def __init__(self):
        self.plugins = SortedDict(lambda k,v: v.priority,reverse=True)
        self.listening_plugins = {}
        self.instances = {}
        self.pconf = {}

    def register(self, name: str, desire_priority: int = 0, **kwargs):
        def wrapper(plugincls):
            plugincls.name = name
            plugincls.priority = desire_priority
            plugincls.desc = kwargs.get('desc')
            plugincls.author = kwargs.get('author')
            plugincls.version = kwargs.get('version') if kwargs.get('version') != None else "1.0"
            plugincls.namecn = kwargs.get('namecn') if kwargs.get('namecn') != None else name
            plugincls.hidden = kwargs.get('hidden') if kwargs.get('hidden') != None else False
            plugincls.enabled = True
            self.plugins[name.upper()] = plugincls
            logger.info("Plugin %s_v%s registered" % (name, plugincls.version))
            return plugincls
        return wrapper

    def save_config(self):
        with open("./plugins/plugins.json", "w", encoding="utf-8") as f:
            json.dump(self.pconf, f, indent=4, ensure_ascii=False)

    def load_config(self):
        logger.info("Loading plugins config...")

        modified = False
        if os.path.exists("./plugins/plugins.json"):
            with open("./plugins/plugins.json", "r", encoding="utf-8") as f:
                pconf = json.load(f)
                pconf['plugins'] = SortedDict(lambda k,v: v["priority"],pconf['plugins'],reverse=True)
        else:
            modified = True
            pconf = {"plugins": SortedDict(lambda k,v: v["priority"],reverse=True)}
        self.pconf = pconf
        if modified:
            self.save_config()
        return pconf

    def scan_plugins(self):
        logger.info("Scaning plugins ...")
        plugins_dir = "./plugins"
        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)
            if os.path.isdir(plugin_path):
                # 判断插件是否包含同名.py文件
                main_module_path = os.path.join(plugin_path, plugin_name+".py")
                if os.path.isfile(main_module_path):
                    # 导入插件
                    import_path = "plugins.{}.{}".format(plugin_name, plugin_name)
                    try:
                        main_module = importlib.import_module(import_path)
                    except Exception as e:
                        logger.warn("Failed to import plugin %s: %s" % (plugin_name, e))
                        continue
        pconf = self.pconf
        new_plugins = []
        modified = False
        for name, plugincls in self.plugins.items():
            rawname = plugincls.name
            if rawname not in pconf["plugins"]:
                new_plugins.append(plugincls)
                modified = True
                logger.info("Plugin %s not found in pconfig, adding to pconfig..." % name)
                pconf["plugins"][rawname] = {"enabled": plugincls.enabled, "priority": plugincls.priority}
            else:
                self.plugins[name].enabled = pconf["plugins"][rawname]["enabled"]
                self.plugins[name].priority = pconf["plugins"][rawname]["priority"]
                self.plugins._update_heap(name) # 更新下plugins中的顺序
        if modified:
            self.save_config()
        return new_plugins

    def refresh_order(self):
        for event in self.listening_plugins.keys():
            self.listening_plugins[event].sort(key=lambda name: self.plugins[name].priority, reverse=True)

    def activate_plugins(self): # 生成新开启的插件实例
        for name, plugincls in self.plugins.items():
            if plugincls.enabled:
                if name not in self.instances:
                    instance = plugincls()
                    self.instances[name] = instance
                    for event in instance.handlers:
                        if event not in self.listening_plugins:
                            self.listening_plugins[event] = []
                        self.listening_plugins[event].append(name)
        self.refresh_order()

    def reload_plugin(self, name:str):
        name = name.upper()
        if name in self.instances:
            for event in self.listening_plugins:
                if name in self.listening_plugins[event]:
                    self.listening_plugins[event].remove(name)
            del self.instances[name]
            self.activate_plugins()
            return True
        return False
    
    def load_plugins(self):
        self.load_config()
        self.scan_plugins()
        pconf = self.pconf
        logger.debug("plugins.json config={}".format(pconf))
        for name,plugin in pconf["plugins"].items():
            if name.upper() not in self.plugins:
                logger.error("Plugin %s not found, but found in plugins.json" % name)
        self.activate_plugins()

    def emit_event(self, e_context: EventContext, *args, **kwargs):
        if e_context.event in self.listening_plugins:
            for name in self.listening_plugins[e_context.event]:
                if self.plugins[name].enabled and e_context.action == EventAction.CONTINUE:
                    logger.debug("Plugin %s triggered by event %s" % (name,e_context.event))
                    instance = self.instances[name]
                    instance.handlers[e_context.event](e_context, *args, **kwargs)
        return e_context

    def set_plugin_priority(self, name:str, priority:int):
        name = name.upper()
        if name not in self.plugins:
            return False
        if self.plugins[name].priority == priority:
            return True
        self.plugins[name].priority = priority
        self.plugins._update_heap(name)
        rawname = self.plugins[name].name
        self.pconf["plugins"][rawname]["priority"] = priority
        self.pconf["plugins"]._update_heap(rawname)
        self.save_config()
        self.refresh_order()
        return True

    def enable_plugin(self, name:str):
        name = name.upper()
        if name not in self.plugins:
            return False
        if not self.plugins[name].enabled :
            self.plugins[name].enabled = True
            rawname = self.plugins[name].name
            self.pconf["plugins"][rawname]["enabled"] = True
            self.save_config()
            self.activate_plugins()
            return True
        return True
    
    def disable_plugin(self, name:str):
        name = name.upper()
        if name not in self.plugins:
            return False
        if self.plugins[name].enabled :
            self.plugins[name].enabled = False
            rawname = self.plugins[name].name
            self.pconf["plugins"][rawname]["enabled"] = False
            self.save_config()
            return True
        return True
    
    def list_plugins(self):
        return self.plugins