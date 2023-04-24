import hashlib
import re
import time

import config
from common.log import logger


def time_checker(f):
    def _time_checker(self, *args, **kwargs):
        _config = config.conf()
        chat_time_module = _config.get("chat_time_module", False)
        if chat_time_module:
            chat_start_time = _config.get("chat_start_time", "00:00")
            chat_stopt_time = _config.get("chat_stop_time", "24:00")
            time_regex = re.compile(r"^([01]?[0-9]|2[0-4])(:)([0-5][0-9])$")  # 时间匹配，包含24:00

            starttime_format_check = time_regex.match(chat_start_time)  # 检查停止时间格式
            stoptime_format_check = time_regex.match(chat_stopt_time)  # 检查停止时间格式
            chat_time_check = chat_start_time < chat_stopt_time  # 确定启动时间<停止时间

            # 时间格式检查
            if not (starttime_format_check and stoptime_format_check and chat_time_check):
                logger.warn("时间格式不正确,请在config.json中修改您的CHAT_START_TIME/CHAT_STOP_TIME,否则可能会影响您正常使用,开始({})-结束({})".format(starttime_format_check, stoptime_format_check))
            if chat_start_time > "23:59":
                logger.error("启动时间可能存在问题，请修改!")

            # 服务时间检查
            now_time = time.strftime("%H:%M", time.localtime())
            if chat_start_time <= now_time <= chat_stopt_time:  # 服务时间内，正常返回回答
                f(self, *args, **kwargs)
                return None
            else:
                if args[0]["Content"] == "#更新配置":  # 不在服务时间内也可以更新配置
                    f(self, *args, **kwargs)
                else:
                    logger.info("非服务时间内,不接受访问")
                    return None
        else:
            f(self, *args, **kwargs)  # 未开启时间模块则直接回答

    return _time_checker
