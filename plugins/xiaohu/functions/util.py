# -*- coding: utf-8 -*-
"""
@Time ： 2023/9/5 15:59
@Auth ： HuangChenjian
@File ：util.py
@IDE ：PyCharm
"""
from functools import lru_cache
import tiktoken
class LazyloadTiktoken(object):
    def __init__(self, model):
        self.model = model

    @staticmethod
    @lru_cache(maxsize=128)
    def get_encoder(model):
        print('正在加载tokenizer，如果是第一次运行，可能需要一点时间下载参数')
        tmp = tiktoken.encoding_for_model(model)
        print('加载tokenizer完毕')
        return tmp

    def encode(self, *args, **kwargs):
        encoder = self.get_encoder(self.model)
        return encoder.encode(*args, **kwargs)

    def decode(self, *args, **kwargs):
        encoder = self.get_encoder(self.model)
        return encoder.decode(*args, **kwargs)
def input_clipping(inputs, history, max_token_limit):
    import numpy as np
    tokenizer_gpt35 = LazyloadTiktoken("gpt-3.5-turbo")
    enc = tokenizer_gpt35
    def get_token_num(txt):
        return len(enc.encode(txt, disallowed_special=()))

    mode = 'input-and-history'
    # 当 输入部分的token占比 小于 全文的一半时，只裁剪历史
    input_token_num = get_token_num(inputs)
    if input_token_num < max_token_limit // 2:
        mode = 'only-history'
        max_token_limit = max_token_limit - input_token_num

    everything = [inputs] if mode == 'input-and-history' else ['']
    everything.extend(history)
    n_token = get_token_num('\n'.join(everything))
    everything_token = [get_token_num(e) for e in everything]
    delta = max(everything_token) // 16  # 截断时的颗粒度

    while n_token > max_token_limit:
        where = np.argmax(everything_token)
        encoded = enc.encode(everything[where], disallowed_special=())
        clipped_encoded = encoded[:len(encoded) - delta]
        everything[where] = enc.decode(clipped_encoded)[:-1]  # -1 to remove the may-be illegal char
        everything_token[where] = get_token_num(everything[where])
        n_token = get_token_num('\n'.join(everything))

    if mode == 'input-and-history':
        inputs = everything[0]
    else:
        pass
    history = everything[1:]
    return inputs, history