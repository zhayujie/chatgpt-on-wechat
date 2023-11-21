from urllib.parse import urlparse
import os


# 获取url后缀
def get_path_suffix(path):
    path = urlparse(path).path
    return os.path.splitext(path)[-1].lstrip('.')
