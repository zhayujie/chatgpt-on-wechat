import os
import signal
import sys
import threading

from channel import channel_factory
from bridge.reply import *
from bridge.context import *
from common import const
from common.log import logger
from config import load_config
from plugins import *

from uvicorn import Server, Config
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# load config
load_config()

# create channel
channel_name = conf().get("channel_type", "wx")

if "--cmd" in sys.argv:
    channel_name = "terminal"

if channel_name == "wxy":
    os.environ["WECHATY_LOG"] = "warn"
    
channel = channel_factory.create_channel(channel_name)

app = FastAPI()

class PublishParams(BaseModel):
    content: str
@app.post('/publish')
async def publish(params: PublishParams):
    filename = 'push_sub_groups.json'
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    success = []
    failed = []
    ignore = []
    for user_id in data: 
        if data[user_id].get("enable") is not True:
            ignore.append(data[user_id].get("nickname"))
            continue
        try:
            channel.send(reply=Reply(
                type=ReplyType.TEXT,
                content=params.content
            ), context={
                'receiver': user_id
            })
            success.append(data[user_id].get("nickname"))
        except Exception as e:
            failed.append(data[user_id].get("nickname"))
            logger.exception(e)
    return JSONResponse({
        "status": 0,
        "message": "OK",
        "result": {
            "success": success,
            "failed": failed,
            "ignore": ignore
        }
    })
    
def start_server():
    # 配置服务器
    server = Server(
        Config(
            app='app:app',
            host='0.0.0.0',
            port=5674,
            log_level=0,
            proxy_headers=True
        )
    )
    server.run()
    
def sigterm_handler_wrap(_signo):
    old_handler = signal.getsignal(_signo)

    def func(_signo, _stack_frame):
        logger.info("signal {} received, exiting...".format(_signo))
        conf().save_user_datas()
        if callable(old_handler):  #  check old_handler
            return old_handler(_signo, _stack_frame)
        sys.exit(0)

    signal.signal(_signo, func)

def main():
    try:
        
        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)
    
        if channel_name in ["wx", "wxy", "terminal", "wechatmp", "wechatmp_service", "wechatcom_app", "wework",
                            const.FEISHU, const.DINGTALK]:
            PluginManager().load_plugins()

        if conf().get("use_linkai"):
            try:
                from common import linkai_client
                threading.Thread(target=linkai_client.start, args=(channel,)).start()
            except Exception as e:
                pass
        
        threading.Thread(target=start_server).start()
        channel.startup()
        
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)
    
if __name__ == '__main__':
    main()