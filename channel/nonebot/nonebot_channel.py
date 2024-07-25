import os
import io
import time

import requests
import nonebot
from nonebot.adapters.onebot.v11 import Adapter, Bot
from pathlib import Path

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from common.singleton import singleton
from common.utils import compress_imgfile, fsize, split_string_by_utf8_length
from config import conf
from common.log import logger
from voice.audio_convert import any_to_amr, split_audio

import asyncio

MAX_UTF8_LEN = 2048


@singleton
class NoneBotChannel(ChatChannel):
    """
    NoneBot消息通道
    """

    def __init__(self):
        super().__init__()
        self.Driver = conf().get("nonebot_driver", "~websockets")  # nonebot驱动
        self.HOST = conf().get("nonebot_listen_host", "127.0.0.1")  # nonebot监听地址
        self.PORT = conf().get("nonebot_listen_port", "1314")  # nonebot监听端口
        self.ACCESS_TOKEN = conf().get("nonebot_access_token")  # nonebot访问令牌
        self.SuperUsers = conf().get("nonebot_superusers", [])  # nonebot超级用户
        self.NickName = conf().get("nonebot_nickname", ["Bot"])  # nonebot昵称
        self.CommandStart = conf().get("nonebot_command_start", ["/"])  # nonebot命令前缀
        self.CommandSep = conf().get("nonebot_command_sep", [" "])  # nonebot命令分隔符

        logger.info(
            "[nonebot] init: driver: {}, host: {}, port: {}, access_token: {}, superusers: {}, nickname: {}, "
            "command_start: {}, command_sep: {}".format(self.Driver, self.HOST, self.PORT, self.ACCESS_TOKEN,
                                                        self.SuperUsers, self.NickName, self.CommandStart,
                                                        self.CommandSep))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        bot: Bot = context['msg'].bot

        is_group = context["msg"].is_group

        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = reply.content
            texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)
            if len(texts) > 1:
                logger.info("[NoneBot] text too long, split into {} parts".format(len(texts)))
            for i, text in enumerate(texts):
                # 发送文本消息
                asyncio.run(bot.send_msg(
                    message_type="group" if is_group else "private",
                    user_id=context["msg"].from_user_id,
                    group_id=receiver if is_group else None,
                    message=text
                ))
                if i != len(texts) - 1:
                    time.sleep(0.5)  # 休眠0.5秒，防止发送过快乱序
            logger.info("[NoneBot] send message to {}: {}".format(context["msg"].from_user_nickname, reply_text))
        elif reply.type == ReplyType.VOICE:
            try:
                media_ids = []
                file_path = reply.content
                amr_file = os.path.splitext(file_path)[0] + ".amr"
                any_to_amr(file_path, amr_file)
                duration, files = split_audio(amr_file, 60 * 1000)
                if len(files) > 1:
                    logger.info("[NoneBot] voice too long, {}s > 60s, split into {} parts".format(duration / 1000.0, len(files)))
                for path in files:
                    # TODO 发送消息 voice
                    time.sleep(1)
            except Exception as e:
                logger.error(f"[NoneBot] send voice failed: {e}")
                return
            try:
                os.remove(file_path)
                if amr_file != file_path:
                    os.remove(amr_file)
            except Exception as e:
                logger.error(f"[NoneBot] remove voice file failed: {e}")
            logger.info(f"[NoneBot] send voice to {context['msg'].from_user_nickname}: {reply.content}")
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[NoneBot] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[NoneBot] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            try:
                # TODO 发送图片
                pass
            except Exception as e:
                logger.error(f"[NoneBot] send image failed: {e}")
                return
            logger.info(f"[NoneBot] send image to {context['msg'].from_user_nickname}: {reply.content}")
        elif reply.type == ReplyType.IMAGE:  # 本地图片
            image_storage = reply.content
            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[NoneBot] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[NoneBot] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            try:
                # TODO 发送图片
                pass
            except Exception as e:
                logger.error(f"[NoneBot] send image failed: {e}")
                return
            logger.info(f"[NoneBot] send image to {context['msg'].from_user_nickname}: {reply.content}")

        # 通过nonebot发送消息
        pass

    def startup(self):
        # 启动nonebot
        nonebot.init(
            driver=self.Driver,
            host=self.HOST,
            port=self.PORT,
            onebot_access_token=self.ACCESS_TOKEN,
            superusers=set(self.SuperUsers),
            nickname=set(self.NickName),
            command_start=set(self.CommandStart),
            command_sep=set(self.CommandSep)
        )

        driver = nonebot.get_driver()
        driver.register_adapter(Adapter)

        # 获取当前运行目录
        # print("=============")
        pyprojectPath = Path(__file__).parent / "pyproject.toml"
        print(pyprojectPath)

        # 加载插件
        # nonebot.load_builtin_plugin("echo")  # 内置插件，用以测试
        nonebot.load_from_toml(str(pyprojectPath), encoding="utf-8")
        # nonebot.load_plugin("none_bot/plugins/chatWithAI/__init__.py")  # 本地插件

        nonebot.run()  # 运行bot
