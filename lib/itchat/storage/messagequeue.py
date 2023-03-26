import logging
try:
    import Queue as queue
except ImportError:
    import queue

from .templates import AttributeDict

logger = logging.getLogger('itchat')

class Queue(queue.Queue):
    def put(self, message):
        queue.Queue.put(self, Message(message))

class Message(AttributeDict):
    def download(self, fileName):
        if hasattr(self.text, '__call__'):
            return self.text(fileName)
        else:
            return b''
    def __getitem__(self, value):
        if value in ('isAdmin', 'isAt'):
            v = value[0].upper() + value[1:] # ''[1:] == ''
            logger.debug('%s is expired in 1.3.0, use %s instead.' % (value, v))
            value = v
        return super(Message, self).__getitem__(value)
    def __str__(self):
        return '{%s}' % ', '.join(
            ['%s: %s' % (repr(k),repr(v)) for k,v in self.items()])
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__.split('.')[-1],
            self.__str__())
