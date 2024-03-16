# encoding:utf-8
import base64
import os
import signal
import sys
import time

from flask import Flask
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from channel import channel_factory
from common import const
from config import load_config
from plugins import *
import threading
from typing import Union
from fastapi import FastAPI
from lib.itchat import *

from PIL import Image


def sigterm_handler_wrap(_signo):
    old_handler = signal.getsignal(_signo)

    def func(_signo, _stack_frame):
        logger.info("signal {} received, exiting...".format(_signo))
        conf().save_user_datas()
        if callable(old_handler):  # check old_handler
            return old_handler(_signo, _stack_frame)
        sys.exit(0)

    signal.signal(_signo, func)


def start_channel(channel_name: str):
    channel = channel_factory.create_channel(channel_name)
    if channel_name in ["wx", "wxy", "terminal", "wechatmp", "wechatmp_service", "wechatcom_app", "wework",
                        const.FEISHU, const.DINGTALK]:
        PluginManager().load_plugins()

    if conf().get("use_linkai"):
        try:
            from common import linkai_client
            threading.Thread(target=linkai_client.start, args=(channel,)).start()
        except Exception as e:
            pass
    channel.startup()


def run(app: Flask):
    try:
        # load config
        load_config()
        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)

        # create channel
        channel_name = conf().get("channel_type", "wx")

        if channel_name == "wx":
            threading.Thread(target=app.run).start()

        if "--cmd" in sys.argv:
            channel_name = "terminal"

        if channel_name == "wxy":
            os.environ["WECHATY_LOG"] = "warn"

        start_channel(channel_name)

        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)


app = Flask(__name__)
@app.route('/wxlogin')
async def wxlogin():
    logger.info("当前是否正在进行登陆？ %s", str(instance.isLogging))

    if instance.isLogging == False and instance.loginInfo.get("User") != None:
        return "已经登陆,当前登陆账号是：" + instance.loginInfo.get("User").NickName
    else:
        imgByte = get_QR()
        # io.BytesIO() 转成 base64
        imgBase = "data:image/png;base64," + str(base64.b64encode(imgByte.getvalue()), 'utf-8')
        return "<img src='" + imgBase + "'>" + "<br>" + "请扫描二维码登陆"


if __name__ == "__main__":
    run(app)
