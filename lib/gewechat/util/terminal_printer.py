import os
import qrcode

def print_green(text):
    print(f"\033[32m{text}\033[0m")

def print_yellow(text):
    print(f"\033[33m{text}\033[0m")

def print_red(text):
    print(f"\033[31m{text}\033[0m")

def make_and_print_qr(url):
    """生成并打印二维码

    Args:
        url: 需要生成二维码的URL字符串

    Returns:
        None

    功能:
        1. 在终端打印二维码的ASCII图形
        2. 同时提供在线二维码生成链接作为备选
        3. 同时在本地当前文件夹tmp下生成二维码
    """
    print_green(f"您可以访问下方链接获取二维码:\nhttps://api.qrserver.com/v1/create-qr-code/?data={url}")
    print_green("也可以扫描下方二维码登录")
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make()
    qr.print_ascii(invert=True)

    img = qrcode.make(data=url)
    if not os.path.exists('tmp'):
        os.makedirs('tmp')
    with open('tmp/login.png', 'wb') as f:
        img.save(f)
