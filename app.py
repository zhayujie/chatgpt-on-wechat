# encoding:utf-8

import os
import signal
import sys
import time

from channel import channel_factory
from common import const
from common.log import logger
from config import load_config, conf
from plugins import *
import threading


# Global channel manager for restart support
_channel_mgr = None


def get_channel_manager():
    return _channel_mgr


class ChannelManager:
    """
    Manage the lifecycle of a channel, supporting restart from sub-threads.
    The channel.startup() runs in a daemon thread so that the main thread
    remains available and a new channel can be started at any time.
    """

    def __init__(self):
        self._channel = None
        self._channel_thread = None
        self._lock = threading.Lock()

    @property
    def channel(self):
        return self._channel

    def start(self, channel_name: str, first_start: bool = False):
        """
        Create and start a channel in a sub-thread.
        If first_start is True, plugins and linkai client will also be initialized.
        """
        with self._lock:
            channel = channel_factory.create_channel(channel_name)
            self._channel = channel

            if first_start:
                if channel_name in ["wx", "wxy", "terminal", "wechatmp", "web",
                                    "wechatmp_service", "wechatcom_app", "wework",
                                    const.FEISHU, const.DINGTALK]:
                    PluginManager().load_plugins()

                if conf().get("use_linkai"):
                    try:
                        from common import cloud_client
                        threading.Thread(target=cloud_client.start, args=(channel, self), daemon=True).start()
                    except Exception as e:
                        pass

            # Run channel.startup() in a daemon thread so we can restart later
            self._channel_thread = threading.Thread(
                target=self._run_channel, args=(channel,), daemon=True
            )
            self._channel_thread.start()
            logger.debug(f"[ChannelManager] Channel '{channel_name}' started in sub-thread")

    def _run_channel(self, channel):
        try:
            channel.startup()
        except Exception as e:
            logger.error(f"[ChannelManager] Channel startup error: {e}")
            logger.exception(e)

    def stop(self):
        """
        Stop the current channel. Since most channel startup() methods block
        on an HTTP server or stream client, we stop by terminating the thread.
        """
        with self._lock:
            if self._channel is None:
                return
            channel_type = getattr(self._channel, 'channel_type', 'unknown')
            logger.info(f"[ChannelManager] Stopping channel '{channel_type}'...")

            # Try graceful stop if channel implements it
            try:
                if hasattr(self._channel, 'stop'):
                    self._channel.stop()
            except Exception as e:
                logger.warning(f"[ChannelManager] Error during channel stop: {e}")

            self._channel = None
            self._channel_thread = None

    def restart(self, new_channel_name: str):
        """
        Restart the channel with a new channel type.
        Can be called from any thread (e.g. linkai config callback).
        """
        logger.info(f"[ChannelManager] Restarting channel to '{new_channel_name}'...")
        self.stop()

        # Clear singleton cache so a fresh channel instance is created
        _clear_singleton_cache(new_channel_name)

        time.sleep(1)  # Brief pause to allow resources to release
        self.start(new_channel_name, first_start=False)
        logger.info(f"[ChannelManager] Channel restarted to '{new_channel_name}' successfully")


def _clear_singleton_cache(channel_name: str):
    """
    Clear the singleton cache for the channel class so that
    a new instance can be created with updated config.
    """
    cls_map = {
        "wx": "channel.wechat.wechat_channel.WechatChannel",
        "wxy": "channel.wechat.wechaty_channel.WechatyChannel",
        "wcf": "channel.wechat.wcf_channel.WechatfChannel",
        "web": "channel.web.web_channel.WebChannel",
        "wechatmp": "channel.wechatmp.wechatmp_channel.WechatMPChannel",
        "wechatmp_service": "channel.wechatmp.wechatmp_channel.WechatMPChannel",
        "wechatcom_app": "channel.wechatcom.wechatcomapp_channel.WechatComAppChannel",
        "wework": "channel.wework.wework_channel.WeworkChannel",
        const.FEISHU: "channel.feishu.feishu_channel.FeiShuChanel",
        const.DINGTALK: "channel.dingtalk.dingtalk_channel.DingTalkChanel",
    }
    module_path = cls_map.get(channel_name)
    if not module_path:
        return
    # The singleton decorator stores instances in a closure dict keyed by class.
    # We need to find the actual class and clear it from the closure.
    try:
        parts = module_path.rsplit(".", 1)
        module_name, class_name = parts[0], parts[1]
        import importlib
        module = importlib.import_module(module_name)
        # The module-level name is the wrapper function from @singleton
        wrapper = getattr(module, class_name, None)
        if wrapper and hasattr(wrapper, '__closure__') and wrapper.__closure__:
            for cell in wrapper.__closure__:
                try:
                    cell_contents = cell.cell_contents
                    if isinstance(cell_contents, dict):
                        cell_contents.clear()
                        logger.debug(f"[ChannelManager] Cleared singleton cache for {class_name}")
                        break
                except ValueError:
                    pass
    except Exception as e:
        logger.warning(f"[ChannelManager] Failed to clear singleton cache: {e}")


def sigterm_handler_wrap(_signo):
    old_handler = signal.getsignal(_signo)

    def func(_signo, _stack_frame):
        logger.info("signal {} received, exiting...".format(_signo))
        conf().save_user_datas()
        if callable(old_handler):  #  check old_handler
            return old_handler(_signo, _stack_frame)
        sys.exit(0)

    signal.signal(_signo, func)


def run():
    global _channel_mgr
    try:
        # load config
        load_config()
        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)

        # create channel
        channel_name = conf().get("channel_type", "wx")

        if "--cmd" in sys.argv:
            channel_name = "terminal"

        if channel_name == "wxy":
            os.environ["WECHATY_LOG"] = "warn"

        _channel_mgr = ChannelManager()
        _channel_mgr.start(channel_name, first_start=True)

        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)


if __name__ == "__main__":
    run()
