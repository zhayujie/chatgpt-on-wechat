# encoding:utf-8

from enum import Enum

class ContextType (Enum):
    TEXT = 1         # 文本消息
    VOICE = 2        # 音频消息
    IMAGE_CREATE = 3 # 创建图片命令
    
    def __str__(self):
        return self.name
class Context:
    def __init__(self, type : ContextType = None , content = None,  kwargs = dict()):
        self.type = type
        self.content = content
        self.kwargs = kwargs

    def __contains__(self, key):
        if key == 'type':
            return self.type is not None
        elif key == 'content':
            return self.content is not None
        else:
            return key in self.kwargs
        
    def __getitem__(self, key):
        if key == 'type':
            return self.type
        elif key == 'content':
            return self.content
        else:
            return self.kwargs[key]
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        if key == 'type':
            self.type = value
        elif key == 'content':
            self.content = value
        else:
            self.kwargs[key] = value

    def __delitem__(self, key):
        if key == 'type':
            self.type = None
        elif key == 'content':
            self.content = None
        else:
            del self.kwargs[key]
    
    def __str__(self):
        return "Context(type={}, content={}, kwargs={})".format(self.type, self.content, self.kwargs)