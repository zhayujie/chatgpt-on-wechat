import os
from multiprocessing import Process
import signal
import time

import gradio as gr

from channel import channel_factory
from common import const
from config import load_config, conf
from plugins import *

current_process_instance = None

def start_channel(channel_name: str):
    channel = channel_factory.create_channel(channel_name)
    available_channels = [
        "wx",
        "terminal",
        "wechatmp",
        "wechatmp_service",
        "wechatcom_app",
        "wework",
        "wechatcom_service",
        const.FEISHU,
        const.DINGTALK
    ]
    if channel_name in available_channels:
        PluginManager().load_plugins()
    channel.startup()

def run():
    try:
        # load config
        load_config()
        # create channel
        channel_name = conf().get("channel_type", "wx")
        start_channel(channel_name)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)

def start_run():
    global current_process_instance

    if current_process_instance is not None and current_process_instance.is_alive():
        os.kill(current_process_instance.pid, signal.SIGTERM)  # 杀掉当前进程
        current_process_instance.join()  # 等待当前进程结束
    
    current_process_instance = Process(target=run)
    current_process_instance.start()
    time.sleep(10)  # 等待进程启动
    return f"重启成功!!"

def get_qrcode_image():
    image_path = 'tmp/login.png'
    if os.path.exists(image_path):
        return image_path
    else:
        return None

def verify_login(username, password):
    correct_username = conf().get("web_ui_username", "dow")
    correct_password = conf().get("web_ui_password", "dify-on-wechat")
    if username == correct_username and password == correct_password:
        return True
    return False

def login(username, password):
    if verify_login(username, password):
        return (
            gr.update(visible=False), 
            gr.update(visible=True), 
            gr.update(visible=True), 
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),  # Hide username input
            gr.update(visible=False),  # Hide password input
            gr.update(visible=False)   # Hide login button
        )
    else:
        return (
            "用户名或密码错误", 
            gr.update(visible=False), 
            gr.update(visible=False), 
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),   # Show username input
            gr.update(visible=True),   # Show password input
            gr.update(visible=True)    # Show login button
        )

with gr.Blocks() as demo:
    username_input = gr.Textbox(label="用户名")
    password_input = gr.Textbox(label="密码", type="password")
    login_button = gr.Button("登录")
    login_status = gr.Textbox(label="登录状态", value="", interactive=False)

    qrcode_image = gr.Image(value=get_qrcode_image(), label="微信二维码", width=400, height=400, visible=False)
    restart_status = gr.Textbox(label="状态", value="启动成功", visible=False)
    
    with gr.Row():
        restart_button = gr.Button("异常退出后请点击此按钮重启", visible=False)
        refresh_button = gr.Button("登录前请点击此按钮刷新二维码", visible=False)  # 添加手动刷新的按钮
    
    login_button.click(
        login, 
        inputs=[username_input, password_input], 
        outputs=[
            login_status, 
            qrcode_image, 
            restart_button, 
            refresh_button,
            restart_status,
            username_input, 
            password_input, 
            login_button
        ]
    )

    restart_button.click(start_run, outputs=restart_status)

    def refresh_image():
        return get_qrcode_image()
    refresh_button.click(refresh_image, outputs=qrcode_image)  # 手动刷新按钮的点击事件

if __name__ == "__main__":
    start_run()
    load_config()
    demo.launch(server_name="0.0.0.0", server_port=conf().get("web_ui_port", 7860))
