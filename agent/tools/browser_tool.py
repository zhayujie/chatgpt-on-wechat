def copy(self):
    """
    Special copy method for browser tool to avoid recreating browser instance.
    
    :return: A new instance with shared browser reference but unique model
    """
    new_tool = self.__class__()
    
    # Copy essential attributes
    new_tool.model = self.model
    new_tool.context = getattr(self, 'context', None)
    new_tool.config = getattr(self, 'config', None)
    
    # Share the browser instance instead of creating a new one
    if hasattr(self, 'browser'):
        new_tool.browser = self.browser
    
    return new_tool 