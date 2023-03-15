# encoding:utf-8

import config
from channel import channel_factory
from common.log import logger


if __name__ == '__main__':
    try:
        # load config
        config.load_config()

        # create channel
        channel = channel_factory.create_channel("wx")

        # startup channel
        channel.startup()
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)
