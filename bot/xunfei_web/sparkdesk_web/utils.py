# -*- coding: UTF-8 -*-
"""
@Project : sparkdesk-api
@File    : utils.py
@Author  : HildaM
@Email   : Hilda_quan@163.com
@Date    : 2023/7/6 15:10
@Description :  common utils
"""
import base64
import json

log_file_name = "sparkdesk_web/log/session_log.json"


def decode(text):
    try:
        decoded_data = base64.b64decode(text).decode('utf-8')
        return decoded_data
    except Exception as e:
        return ''


def load_log():
    try:
        with open(log_file_name, "r", encoding='utf-8') as f:
            log_data = json.load(f)
            chat_id = log_data["chat_id"]
        return True, chat_id
    except:
        return False, ""


def save_log(chat_id):
    session_log = {"chat_id": chat_id}
    with open(log_file_name, "w", encoding='utf-8') as f:
        json.dump(session_log, f, ensure_ascii=False, indent=4)
