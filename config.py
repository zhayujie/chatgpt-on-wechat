# encoding:utf-8

import json
import os
from common.log import logger

config = {}


def load_config():
    global config
    config_path = "config.json"
    try:
        if not os.path.exists(config_path):
            logger.error('配置文件路径不存在')
            return
        config_str = read_file(config_path)
        # 将json字符串反序列化为dict类型
        config = json.loads(config_str)
        logger.info("[INIT] load config: {}".format(config))
    except Exception as e:
        logger.error(e)


def get_root():
    return os.path.dirname(os.path.abspath( __file__ ))


def read_file(path):
    with open(path, mode='r', encoding='utf-8') as f:
        return f.read()


def conf():
    return config