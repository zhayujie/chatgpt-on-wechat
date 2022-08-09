from channel import channel_factory

if __name__ == '__main__':
    # create channel
    channel = channel_factory.create_channel("wx")

    # startup channel
    channel.startup()

    print("Hello bot")