# encoding:utf-8

import os
from config import conf, load_config
from channel import channel_factory
from common.log import logger

from plugins import *

def run():
    try:
        # load config
        load_config()

        # create channel
        channel_name=conf().get('channel_type', 'wx')
        if channel_name == 'wxy':
            os.environ['WECHATY_LOG']="warn"
            # os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '127.0.0.1:9001'

        channel = channel_factory.create_channel(channel_name)
        if channel_name in ['wx','wxy']:
            PluginManager().load_plugins()

        # startup channel
        channel.startup()
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)

if __name__ == '__main__':
    run()