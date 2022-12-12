import config
from channel import channel_factory

if __name__ == '__main__':
    # load config
    config.load_config()

    # create channel
    channel = channel_factory.create_channel("wx")

    # startup channel
    channel.startup()
