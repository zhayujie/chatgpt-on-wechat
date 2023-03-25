import logging
import sys
import os


def _get_logger():
    log = logging.getLogger('log')
    log.setLevel(logging.INFO)
    console_handle = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter('[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s',
                                                  datefmt='%Y-%m-%d %H:%M:%S')
    console_handle.setFormatter(log_formatter)

    if not os.path.exists(".log"):
        os.makedirs(".log")
    file_handle = logging.FileHandler(".log/robot.log",mode="a", encoding="utf_8")
    file_handle.setLevel(logging.DEBUG)
    file_handle.setFormatter(log_formatter)

    log.addHandler(console_handle)
    log.addHandler(file_handle)
    return log


# 日志句柄
logger = _get_logger()