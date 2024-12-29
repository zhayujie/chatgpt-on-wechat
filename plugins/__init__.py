from .event import *
from .plugin import *
from .plugin_manager import PluginManager

instance = PluginManager()

register = instance.register
# load_plugins                = instance.load_plugins
# emit_event                  = instance.emit_event
