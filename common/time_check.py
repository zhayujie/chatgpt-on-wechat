import time,re,hashlib
from config import load_config,md5,conf
import config


def get_file_md5(file_name):
    """
    计算文件的md5
    :param file_name:
    :return m.hexdigest():
    """
    m = hashlib.md5()   #创建md5对象
    with open(file_name,'rb') as fobj:
        while True:
            data = fobj.read(1024)
            if not data:
                break
            m.update(data)  #更新md5对象
 
    return m.hexdigest()    #返回md5值


def time_checker(f):
    # print(args[0]())
    def wrapTheFunction(self, *args, **kwargs):
        global md5  # 从config.py拿来一个全局变量md5  默认是False
        if md5 == None:
            _config = conf()
        elif md5 == get_file_md5("./config.json"):
            _config = conf()
            # chat_time_module = _config["chat_time_module"]
            # chat_start_time = _config["chat_start_time"]
            # chat_stopt_time = _config["chat_stop_time"]
        else:
            print("检测到配置文件变化")
            _config = load_config()  # 启动时间支持热更改  修改config.json文件后即可生效
            md5 = get_file_md5("./config.json")
            # config.md5 = get_file_md5("./config.json")
        
        chat_time_module = _config["chat_time_module"]
        chat_start_time = _config["chat_start_time"]
        chat_stopt_time = _config["chat_stop_time"]
        # print(md5,chat_time_module,chat_start_time,chat_stopt_time)

        if chat_time_module:
            time_regex = re.compile(r'^([01]?[0-9]|2[0-4])(:)([0-5][0-9])$')  #时间匹配，包含24:00

            starttime_format_check = time_regex.match(chat_start_time)  # 检查停止时间格式
            stoptime_format_check = time_regex.match(chat_stopt_time)  # 检查停止时间格式
            chat_time_check = chat_start_time < chat_stopt_time # 确定启动时间<停止时间

            if starttime_format_check and stoptime_format_check and chat_time_check:
                # print('服务启动时间：{}'.format(CHAT_START_TIME))
                # print('服务结束时间：{}'.format(CHAT_STOP_TIME))
                if chat_start_time>"23:59":
                    print('启动时间可能存在问题，请修改')
            else:
                print("时间格式不正确,请在config.json中修改您的CHAT_START_TIME/CHAT_STOP_TIME,否则可能会影响您正常使用,程序正在自动退出")

            now_time = time.strftime("%H:%M", time.localtime())
            if chat_start_time <= now_time <= chat_stopt_time:
                # print("在服务时间内")
                # 正常请求并返回
                f(self, *args, **kwargs)
                return None
            else:
                print('不在服务时间内,禁止访问')
                return None
        else:
            f(self, *args, **kwargs)
    return wrapTheFunction

