# encoding:utf-8

import json
import logging
import os

class TimeTaskConfig(dict):
    def __init__(self, d=None):
        super().__init__()
        if d is None:
            d = {}
        for k, v in d.items():
            self[k] = v
        
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError as e:
            return default
        except Exception as e:
            raise e
            
config = TimeTaskConfig()

def load_config():
    global config
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    if not os.path.exists(config_path):
        logging.info("配置文件不存在，将使用config-template.json模板")
        config_path = os.path.join(curdir, "config-template.json")

    config_str = read_file(config_path)
    logging.info("[timetask - INIT] config str: {}".format(config_str))

    # 将json字符串反序列化为dict类型
    config = TimeTaskConfig(json.loads(config_str))


def read_file(path):
    with open(path, mode="r", encoding="utf-8") as f:
        return f.read()

def conf():
    return config

