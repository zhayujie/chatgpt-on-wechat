# encoding:utf-8

import config
from channel import channel_factory
from common.log import logger

from plugins import *

def run():
    try:
        # load config
        config.load_config()

        # create channel
        channel_name='wx'
        channel = channel_factory.create_channel(channel_name)
        if channel_name=='wx':
            PluginManager().load_plugins()

        # startup channel
        channel.startup()
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)

if __name__ == '__main__':
    run()