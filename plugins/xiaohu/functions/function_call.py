import json
import os
import openai

from config import conf, load_config


class FunctionCall:
    def __init__(self):
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("open_ai_api_base"):
            openai.api_base = conf().get("open_ai_api_base")
        proxy = conf().get("proxy")
        if proxy:
            openai.proxy = proxy
        self.args = {
            "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # "max_tokens":4096,  # 回复最大的字符数
            "top_p": conf().get("top_p", 1),
            "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }
    def func_call(self, context):
        """
        调用函数
        return: function_name, function_args
        """
        path = os.path.dirname(__file__)
        functions_path = os.path.join(path, 'functions.json')
        with open(functions_path, 'r', encoding="utf-8") as f:
            functions = json.load(f)
        input_messages = []
        promt1 = {"role": "system",
                  "content": "请判断用户输入是否需要调用函数，如果不需要直接返回不需要调用函数，不用你自己进行解答！"}
        promt2 = {"role": "user", "content": context}
        input_messages.extend([promt1, promt2])
        response = openai.ChatCompletion.create(
            model=self.args["model"],
            messages=input_messages,
            functions=functions,
            function_call="auto",
        )
        message = response["choices"][0]["message"]
        # 检查模型是否希望调用函数
        if message.get("function_call"):
            function_name = message["function_call"]["name"]
            function_args = json.loads(message["function_call"].get("arguments", "{}"))
            return function_name, function_args
        else:
            return None, None
if __name__ == '__main__':

    fc = FunctionCall()
    print(fc.func_call("我想要翻译一段话"))