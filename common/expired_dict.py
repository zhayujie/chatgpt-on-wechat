import time
from collections import OrderedDict


class ExpiredDict(OrderedDict):
    def __init__(self, expires_in_seconds):
        super().__init__()
        # 存储键值对的生存时间
        self.expires_in_seconds = expires_in_seconds
        # 获取当前时间的函数
        self.now = time.monotonic

    def __getitem__(self, key):
        # 检查键是否存在
        if key not in self:
            raise KeyError(key)
        # 获取值和过期时间
        value, expiry_time = self[key]
        # 如果过期时间早于当前时间，删除该键值对并引发 KeyError
        if expiry_time is not None and self.now() > expiry_time:
            del self[key]
            raise KeyError(key)
        # 如果存活时间不为 None，更新该键值对的过期时间
        if self.expires_in_seconds is not None:
            self[key] = value, self.now() + self.expires_in_seconds
        # 删除过期的键值对
        self._delete_expired_items()
        # 返回值
        return value

    def __setitem__(self, key, value):
        # 如果存活时间不为 None，设置该键值对的过期时间
        if self.expires_in_seconds is not None:
            self[key] = value, self.now() + self.expires_in_seconds
        else:
            self[key] = value, None
        # 删除过期的键值对
        self._delete_expired_items()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def _delete_expired_items(self):
        # 遍历所有键值对，删除过期的键值对
        for key, (value, expiry_time) in list(self.items()):
            if expiry_time is not None and self.now() > expiry_time:
                del self[key]
