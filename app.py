# encoding:utf-8

import config
from channel import channel_factory
from common.log import logger
import sys
from plugins import *
if __name__ == '__main__':
    channel_name = 'UnDefined'
    try:
        # load config
        config.load_config()
        channel_name = sys.argv[1]
        # create channel
        channel = channel_factory.create_channel(channel_name)
        if channel_name=='wx':
            PluginManager().load_plugins()

        # startup channel
        channel.startup()
    except Exception as e:
        logger.error("App startup failed! channel is " + channel_name)
        logger.exception(e)
