import io
import re
import os
from typing import List, Dict

from urllib.parse import urlparse
from PIL import Image
from common.log import logger

def fsize(file):
    if isinstance(file, io.BytesIO):
        return file.getbuffer().nbytes
    elif isinstance(file, str):
        return os.path.getsize(file)
    elif hasattr(file, "seek") and hasattr(file, "tell"):
        pos = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(pos)
        return size
    else:
        raise TypeError("Unsupported type")


def compress_imgfile(file, max_size):
    if fsize(file) <= max_size:
        return file
    file.seek(0)
    img = Image.open(file)
    rgb_image = img.convert("RGB")
    quality = 95
    while True:
        out_buf = io.BytesIO()
        rgb_image.save(out_buf, "JPEG", quality=quality)
        if fsize(out_buf) <= max_size:
            return out_buf
        quality -= 5


def split_string_by_utf8_length(string, max_length, max_split=0):
    encoded = string.encode("utf-8")
    start, end = 0, 0
    result = []
    while end < len(encoded):
        if max_split > 0 and len(result) >= max_split:
            result.append(encoded[start:].decode("utf-8"))
            break
        end = min(start + max_length, len(encoded))
        # 如果当前字节不是 UTF-8 编码的开始字节，则向前查找直到找到开始字节为止
        while end < len(encoded) and (encoded[end] & 0b11000000) == 0b10000000:
            end -= 1
        result.append(encoded[start:end].decode("utf-8"))
        start = end
    return result


def get_path_suffix(path):
    path = urlparse(path).path
    return os.path.splitext(path)[-1].lstrip('.')


def convert_webp_to_png(webp_image):
    from PIL import Image
    try:
        webp_image.seek(0)
        img = Image.open(webp_image).convert("RGBA")
        png_image = io.BytesIO()
        img.save(png_image, format="PNG")
        png_image.seek(0)
        return png_image
    except Exception as e:
        logger.error(f"Failed to convert WEBP to PNG: {e}")
        raise

def print_green(text):
    print(f"\033[32m{text}\033[0m")

def print_yellow(text):
    print(f"\033[33m{text}\033[0m")

def print_red(text):
    print(f"\033[31m{text}\033[0m")

def parse_markdown_text(text: str) -> List[Dict]:
    """
    解析包含图片和文件链接的混合内容文本。code by sonnet3.5

    参数:
    text (str): Markdown格式文本，包含图片和文件链接

    返回:
    list: 包含不同类型内容（文本、图片、文件）的字典列表，每个字典包含类型和内容键值对

    example:

    text = "这是一篇图片与文件混合的文章\n这是图片1 ![Image1](/file/path/1.jpg)\n这是文件1 [file1](https://example.com/file.pdf)\n这是剩余的部分\n文件2 [file2](/file/path/2.docx)\n这是图片2 ![Image2](https://example.com/image2.png) 末尾文本")
    result = [
        {
            "type": "text",
            "content": "这是一篇图片与文件混合的文章\n    这是图片1"
        },
        {
            "type": "image",
            "content": "/file/path/1.jpg"
        },
        {
            "type": "text",
            "content": "这是文件1"
        },
        {
            "type": "file",
            "content": "https://example.com/file.pdf"
        },
        {
            "type": "text",
            "content": "这是剩余的部分\n    文件2"
        },
        {
            "type": "file",
            "content": "/file/path/2.docx"
        },
        {
            "type": "text",
            "content": "这是图片2"
        },
        {
            "type": "image",
            "content": "https://example.com/image2.png"
        },
        {
            "type": "text",
            "content": "末尾文本"
        }
    ]
    """

    # 定义正则表达式模式，匹配图片和文件链接的Markdown语法
    # (!\[.*?\]\((.*?)\)) 匹配图片: ![alt text](url)
    # (\[.*?\]\((.*?)\)) 匹配文件链接: [text](url)
    pattern = r'(!\[.*?\]\((.*?)\)|\[.*?\]\((.*?)\))'
    
    # 使用正则表达式分割文本
    # 这将产生一个列表，其中包含文本、完整匹配、图片URL和文件URL
    parts = re.split(pattern, text)
    
    # 初始化结果列表和当前文本变量
    result = []
    current_text = ""
    
    # 遍历分割后的部分，每次跳过4个元素
    # 因为每个匹配项产生4个部分：文本、完整匹配、图片URL（如果有）、文件URL（如果有）
    for i in range(0, len(parts), 4):
        # 如果存在文本部分，添加到当前文本
        if parts[i].strip():
            current_text += parts[i].strip()
        
        # 检查是否存在匹配项（图片或文件）
        if i + 1 < len(parts) and parts[i + 1]:
            # 如果有累积的文本，添加到结果列表
            if current_text:
                result.append({"type": "text", "content": current_text})
                current_text = ""  # 重置当前文本
            
            # 检查是否为图片
            if parts[i + 2]:
                result.append({"type": "image", "content": parts[i + 2]})
            # 如果不是图片，则为文件
            elif parts[i + 3]:
                result.append({"type": "file", "content": parts[i + 3]})
    
    # 处理最后可能剩余的文本
    if current_text:
        result.append({"type": "text", "content": current_text})
    return result

def remove_markdown_symbol(text: str):
    # 移除markdown格式，目前先移除**
    if not text:
        return text
    return re.sub(r'\*\*(.*?)\*\*', r'\1', text)
