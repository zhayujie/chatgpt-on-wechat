# -*- coding: UTF-8 -*-
"""
@Project : sparkdesk-api
@File    : core.py
@Author  : HildaM
@Email   : Hilda_quan@163.com
@Date    : 2023/7/6 15:00
@Description : web接口核心入口
"""
import json
import os
import sys
from datetime import datetime
import requests
from pyhandytools.file import FileUtils
from sparkdesk_web.utils import decode
from sparkdesk_web.web import create_chat_header, create_request_header

NEW_CHAT = "SparkDesk AI chat"


class SparkWeb:
    __cookie = ""
    __fd = ""
    __GtToken = ""
    __chat_id = ""
    __chat_header = ""
    __request_header = ""
    __chat_history = list()

    def __init__(self, cookie, fd, GtToken, ChatID=""):
        self.__cookie = cookie
        self.__fd = fd
        self.__GtToken = GtToken
        self.__cha_header = create_chat_header(cookie)
        self.__request_header = create_request_header(cookie)
        self.__chat_id = ChatID

    def __generate_chat_id(self):
        if self.__chat_id == "":
            url = 'https://xinghuo.xfyun.cn/iflygpt/u/chat-list/v1/create-chat-list'
            payload = "{}"
            response = requests.request("POST", url, headers=self.__request_header, data=payload)
            response_data = json.loads(response.text)
            if response_data['code'] == 0:
                chat_list_id = response_data['data']['id']
                return chat_list_id
            else:
                return '0'
        else:
            return self.__chat_id

    def __set_name(self, chat_name):
        url = "https://xinghuo.xfyun.cn/iflygpt/u/chat-list/v1/rename-chat-list"
        chat_list_name = chat_name[:15]
        payload = {
            'chatListId': self.__chat_id,
            'chatListName': chat_list_name,
        }
        response = requests.request("POST", url, headers=self.__request_header, data=json.dumps(payload))
        response_data = json.loads(response.text)
        if response_data['code'] != 0:
            print('\nERROR: Failed to initialize session name. Please reset Cookie, fd and GtToken')
            exit(-1)

    def __create_chat(self, chat_name):
        self.__chat_id = self.__generate_chat_id()
        self.__set_name(chat_name)

    # 获取最近一次的sid用于延续对话，否则对话无记忆
    def __get_chat_sid(self) -> str:
        try:
            response = self.__get_chat_history()
            data = json.loads(response.text)
            return data['data'][-1]["historyList"][-1]["sid"]
        except:
            return ''

    def __get_chat_history(self):

        url = f'https://xinghuo.xfyun.cn/iflygpt/u/chat_history/all/{self.__chat_id}'
        response = requests.request("GET", url, headers=self.__request_header)
        return response

    def __get_resp(self, question):

        sid = self.__get_chat_sid()
        url = "https://xinghuo.xfyun.cn/iflygpt-chat/u/chat_message/chat"
        payload = {
            'fd': self.__fd,
            'chatId': self.__chat_id,
            'text': question,
            'GtToken': self.__GtToken,
            'sid': sid,
            'clientType': '1'
        }
        response = requests.request("POST", url, headers=self.__cha_header, data=payload, stream=True)
        return response

    def chat(self, question):
        self.__create_chat(NEW_CHAT)

        response = self.__get_resp(question)
        response_text = ''
        for line in response.iter_lines():
            if line:
                encoded_data = line[len("data:"):]
                missing_padding = len(encoded_data) % 4
                if missing_padding != 0:
                    encoded_data += b'=' * (4 - missing_padding)
                if decode(encoded_data) != 'zw':
                    sys.stdout.flush()
                    answer = decode(encoded_data).replace('\n\n', '\n')
                    response_text += answer

        if len(response_text.strip()) == 0:
            print("WARNING: 可能触发敏感词监控，对话已被重置，请前往Web页面更新Cookie、fd、GtToken！")
        return response_text

    def __streaming_output(self, question):
        response = self.__get_resp(question)
        response_text = ''
        for line in response.iter_lines():
            if line:
                encoded_data = line[len("data:"):]
                missing_padding = len(encoded_data) % 4
                if missing_padding != 0:
                    encoded_data += b'=' * (4 - missing_padding)
                if decode(encoded_data) != 'zw':
                    sys.stdout.flush()
                    answer = decode(encoded_data).replace('\n\n', '\n')
                    response_text += answer
                    print(answer, end="")
        if len(response_text.strip()) == 0:
            return '', False
        print("\n")
        return response_text, True

    def chat_stream(self, history: bool = False, history_path: str = './history/'):
        history_file_path = ''
        if history:
            FileUtils.check_dir_path(history_path)
            history_file_path = os.path.join(history_path, f'history_{str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))}.json')
        try:
            self.__create_chat(NEW_CHAT)
            print("Enter exit or stop to end the conversation.\n")
            count = 0
            while True:
                count += 1
                question = input("Ask: ")
                if question == 'exit' or question == 'stop':
                    break
                resp = self.__streaming_output(question)
                # If False, regenerate the chat
                if resp[1] is False:
                    print("WARNING: 可能触发敏感词监控，对话已被重置，请前往Web页面更新Cookie、fd、GtToken！")
                if history:
                    self.__chat_history.append({
                        'time': str(datetime.now()),
                        'question': question,
                        'answer': resp[0] if resp[0] else '触发敏感词监控'
                    })
        finally:
            if history:
                FileUtils.write2json(history_file_path, self.__chat_history)
            print("\nThank you for using the SparkDesk AI. Welcome to use it again!")

    # 提供连续对话
    def create_continuous_chat(self):
        # 生成器包装，提供预激服务
        class ContextGenWrapper:
            def __init__(self, spark, gen):
                self._gen = gen
                self._spark = spark
                # 第一次构建生成器 进行预激
                next(gen)

            def chat(self, question):
                result = self._gen.send(question)
                # 将生成器执行到接受question的位置
                self._gen.send(None)
                return result

        return ContextGenWrapper(self, self.continuous_chat_gen())

    # 连续对话生成器
    def continuous_chat_gen(self):
        self.__create_chat(NEW_CHAT)
        count = 0
        while True:
            count += 1
            question = yield
            resp = self.__streaming_output(question)
            # If False, regenerate the chat
            if resp[1] is False:
                print("WARNING: 可能触发敏感词监控，对话已被重置，请前往Web页面更新Cookie、fd、GtToken！")
            yield resp[0]
