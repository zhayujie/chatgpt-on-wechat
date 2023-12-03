# coding=utf-8
"""
Author: chazzjimel
Email: chazzjimel@gmail.com
wechat：cheung-z-x

Description:

"""
import json
import time

import requests
import datetime
import hashlib
import hmac
import base64
import urllib.parse
import uuid

from common.log import logger
from common.tmp_dir import TmpDir


def text_to_speech_aliyun(url, text, appkey, token):
    # 请求的headers
    headers = {
        "Content-Type": "application/json",
    }

    # 请求的payload
    data = {
        "text": text,
        "appkey": appkey,
        "token": token,
        "format": "wav"
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # 检查响应状态码和内容类型
    if response.status_code == 200 and response.headers['Content-Type'] == 'audio/mpeg':
        # 构造唯一的文件名
        output_file = TmpDir().path() + "reply-" + str(int(time.time())) + "-" + str(hash(text) & 0x7FFFFFFF) + ".wav"

        # 将响应内容写入文件
        with open(output_file, 'wb') as file:
            file.write(response.content)
        logger.debug(f"音频文件保存成功，文件名：{output_file}")
    else:
        # 打印错误信息
        logger.debug("响应状态码: {}".format(response.status_code))
        logger.debug("响应内容: {}".format(response.text))
        output_file = None

    return output_file


class AliyunTokenGenerator:
    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def sign_request(self, parameters):
        # 将参数排序
        sorted_params = sorted(parameters.items())

        # 构造待签名的字符串
        canonicalized_query_string = ''
        for (k, v) in sorted_params:
            canonicalized_query_string += '&' + self.percent_encode(k) + '=' + self.percent_encode(v)

        string_to_sign = 'GET&%2F&' + self.percent_encode(canonicalized_query_string[1:])  # 使用GET方法

        # 计算签名
        h = hmac.new((self.access_key_secret + "&").encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1)
        signature = base64.encodebytes(h.digest()).strip()

        return signature

    def percent_encode(self, encode_str):
        encode_str = str(encode_str)
        res = urllib.parse.quote(encode_str, '')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

    def get_token(self):
        # 设置请求参数
        params = {
            'Format': 'JSON',
            'Version': '2019-02-28',
            'AccessKeyId': self.access_key_id,
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'SignatureVersion': '1.0',
            'SignatureNonce': str(uuid.uuid4()),  # 使用uuid生成唯一的随机数
            'Action': 'CreateToken',
            'RegionId': 'cn-shanghai'
        }

        # 计算签名
        signature = self.sign_request(params)
        params['Signature'] = signature

        # 构造请求URL
        url = 'http://nls-meta.cn-shanghai.aliyuncs.com/?' + urllib.parse.urlencode(params)

        # 发送请求
        response = requests.get(url)

        return response.text
