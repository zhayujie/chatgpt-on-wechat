import os
from bridge.reply import Reply, ReplyType
from config import conf
from langchain.utilities import GoogleSerperAPIWrapper
import plugins
from plugins import *


@plugins.register(
    name="GoogleSearch",
    desire_priority=1,
    hidden=False,
    desc="A plugin that fetches daily search",
    version="0.1",
    author="YourName",
)
class GoogleSearch(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        print("[GoogleSearch] inited")
        
    def on_handle_context(self, e_context: EventContext):
        content = e_context["context"].content
        if content.startswith("搜索 "):
            parts = content.split(" ")
            self.command = parts[1]
            os.environ["SERPER_API_KEY"] = conf().get("serper_api_key")
            search = GoogleSerperAPIWrapper()
            response = search.run(self.command)

            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = response
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
        else:
          print("ERROR: Data not found in response")
        
    
    def get_help_text(self, **kwargs):
        help_text = "输入 '搜索 <你需要搜索的内容>'，我会为搜索\n"
        return help_text
      