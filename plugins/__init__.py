from .plugin_manager import PluginManager
from .event import *
from .plugin import *

instance = PluginManager()

register                    = instance.register
# load_plugins                = instance.load_plugins
# emit_event                  = instance.emit_event
