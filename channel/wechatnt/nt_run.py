import sys
import os
import time

os.environ['ntchat_LOG'] = "ERROR"

import ntchat

wechatnt = ntchat.WeChat()


def forever():
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ntchat.exit_()
        os._exit(0)
        # sys.exit(0)
