import logging

class LogSystem(object):
    handlerList = []
    showOnCmd = True
    loggingLevel = logging.INFO
    loggingFile = None
    def __init__(self):
        self.logger = logging.getLogger('itchat')
        self.logger.addHandler(logging.NullHandler())
        self.logger.setLevel(self.loggingLevel)
        self.cmdHandler = logging.StreamHandler()
        self.fileHandler = None
        self.logger.addHandler(self.cmdHandler)
    def set_logging(self, showOnCmd=True, loggingFile=None,
            loggingLevel=logging.INFO):
        if showOnCmd != self.showOnCmd:
            if showOnCmd:
                self.logger.addHandler(self.cmdHandler)
            else:
                self.logger.removeHandler(self.cmdHandler)
            self.showOnCmd = showOnCmd
        if loggingFile != self.loggingFile:
            if self.loggingFile is not None: # clear old fileHandler
                self.logger.removeHandler(self.fileHandler)
                self.fileHandler.close()
            if loggingFile is not None: # add new fileHandler
                self.fileHandler = logging.FileHandler(loggingFile)
                self.logger.addHandler(self.fileHandler)
            self.loggingFile = loggingFile
        if loggingLevel != self.loggingLevel:
            self.logger.setLevel(loggingLevel)
            self.loggingLevel = loggingLevel

ls = LogSystem()
set_logging = ls.set_logging
