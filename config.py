# encoding:utf-8

import json
import os
from common.log import logger

config = {}

def load_config():
    global config
    config_path = "./config.json"
    if not os.path.exists(config_path):
        logger.info('配置文件不存在，将使用config-template.json模板')
        config_path = "./config-template.json"

    config_str = read_file(config_path)
    # 将json字符串反序列化为dict类型
    config = json.loads(config_str)

    # override config with environment variables.
    # Some online deployment platforms (e.g. Railway) deploy project from github directly. So you shouldn't put your secrets like api key in a config file, instead use environment variables to override the default config.
    for name, value in os.environ.items():
        config[name] = value

    logger.info("[INIT] load config: {}".format(config))



def get_root():
    return os.path.dirname(os.path.abspath( __file__ ))


def read_file(path):
    with open(path, mode='r', encoding='utf-8') as f:
        return f.read()


def conf():
    return config
