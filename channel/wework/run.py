import os
import time
os.environ['ntwork_LOG'] = "ERROR"
import ntwork

wework = ntwork.WeWork()


def forever():
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        ntwork.exit_()
        os._exit(0)


