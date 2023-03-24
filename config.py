# encoding:utf-8
from common.log import logger
import json
import os


def load_modes():
  with open('modes.json', 'r', encoding='utf-8') as f:
    modes = json.load(f)
  return modes


def save_modes(modes):
  with open('modes.json', 'w', encoding='utf-8') as f:
    json.dump(modes, f, indent=4, ensure_ascii=False)


def load_config():
  if not os.path.exists('config.json'):
    logger.error('配置文件不存在，请根据config-template.json模板创建config.json文件')
  with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
  return config


def save_config(conf):
  with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(conf, f, indent=4, ensure_ascii=False)


conf = load_config
