import logging
import sys
import os

_logLevel = os.environ.get('CHATGPT_LOG_LEVEL')
logLevel = logging.INFO
if _logLevel is not None:
    logLevel = int(_logLevel)

def _get_logger():
    log = logging.getLogger('log')
    log.setLevel(logLevel)
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(logging.Formatter('[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s',
                                                  datefmt='%Y-%m-%d %H:%M:%S'))
    log.addHandler(console_handle)
    return log


# 日志句柄
logger = _get_logger()