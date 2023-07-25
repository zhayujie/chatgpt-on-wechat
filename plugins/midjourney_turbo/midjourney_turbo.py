#!/usr/bin/env python
# -*- coding=utf-8 -*-
"""
@time: 2023/5/25 10:46
@Project ：chatgpt-on-wechat
@file: midjourney_turbo.py
"""
import base64
import datetime
import json
import re
import sqlite3
import threading
import time
import openai
import requests
import io
import os

from PIL import Image
from plugins.midjourney_turbo.lib.midJourney_module import MidJourneyModule
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.wechatcom.wechatcomapp_channel import WechatComAppChannel
from channel.wechat.wechat_channel import WechatChannel
from channel.wechatmp.wechatmp_channel import WechatMPChannel
from config import conf
import plugins
from plugins import *
from common.log import logger
from common.expired_dict import ExpiredDict
from datetime import timedelta


# 创建并返回相应类型的频道对象
def create_channel_object():
    # 从配置中获取频道类型
    channel_type = conf().get("channel_type")
    # 根据频道类型创建相应的频道对象
    if channel_type in ['wechat', 'wx', 'wxy']:
        return WechatChannel(), ReplyType.IMAGE, 1
    elif channel_type == 'wechatmp':
        return WechatMPChannel(), ReplyType.IMAGE_URL, 2
    elif channel_type == 'wechatmp_service':
        return WechatMPChannel(), ReplyType.IMAGE_URL, 2
    elif channel_type == 'wechatcom_app':
        return WechatComAppChannel(), ReplyType.IMAGE_URL, 2
    else:
        return WechatChannel(), ReplyType.IMAGE, 1


# 对内容进行格式化处理
def format_content(content):
    # 将内容中的"—"替换为"--"
    if "—" in content:
        content = content.replace("—", "--")
    # 如果内容中包含"--"，则按"--"将内容分割为提示和命令两部分
    if "--" in content:
        prompt, commands = content.split("--", 1)
        commands = " --" + commands.strip()
    else:
        prompt, commands = content, ""

    return prompt, commands


# 根据内容生成提示信息
def generate_prompt(content):
    # 创建提示信息的内容
    message_content = "请根据AI生图关键词'{}'预测想要得到的画面，然后用英文拓展描述、丰富细节、添加关键词描述以适用于AI生图。描述要简短直接突出重点，请把优化后的描述直接返回，不需要多余的语言！".format(
        content)
    # 创建一个openai聊天完成的对象，并获取返回的内容
    completion = openai.ChatCompletion.create(model=conf().get("model"), messages=[
        {"role": "user", "content": message_content}], max_tokens=300, temperature=0.8, top_p=0.9)
    prompt = completion['choices'][0]['message']['content']
    logger.debug("优化后的关键词：{}".format(prompt))
    return prompt


# 将图片转换为base64编码的字符串
def convert_base64(image):
    # 打开图片文件
    with open(image, "rb") as image_file:
        # 对图片内容进行base64编码
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')


# 下载并压缩图片
def download_and_compress_image(url, filename, quality=30):
    # 确定保存图片的目录
    directory = os.path.join(os.getcwd(), "tmp")
    # 如果目录不存在，则创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 下载图片
    response = requests.get(url)
    image = Image.open(io.BytesIO(response.content))

    # 压缩图片
    image_path = os.path.join(directory, f"{filename}.jpg")
    image.save(image_path, "JPEG", quality=quality)

    return image_path


# 带有重试机制的发送消息
def send_with_retry(comapp, com_reply, e_context, max_retries=3, delay=2):
    # 尝试发送消息，如果失败则重试
    for i in range(max_retries):
        try:
            # 尝试发送消息
            comapp.send(com_reply, e_context['context'])
            break  # 如果成功发送，就跳出循环
        except requests.exceptions.SSLError as e:
            # 如果因为SSL错误而发送失败，记录错误并重试
            logger.error(f"Failed to send message due to SSL error: {e}. Attempt {i + 1} of {max_retries}")
            if i < max_retries - 1:  # 如果不是最后一次尝试，那么等待一段时间再重试
                time.sleep(delay)  # 等待指定的秒数
            else:
                # 如果尝试发送消息的次数达到了最大次数，记录错误并放弃
                logger.error(f"Failed to send message after {max_retries} attempts. Giving up.")


# 使用装饰器注册一个名为"Midjourney_Turbo"的插件
@plugins.register(name="Midjourney_Turbo", desc="使用Midjourney来画图", desire_priority=1, version="3.1",
                  author="chazzjimel")
# 定义一个名为 MidjourneyTurbo 的类，继承自 Plugin
class MidjourneyTurbo(Plugin):
    # 初始化类
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        try:
            # 获取当前文件的目录
            curdir = os.path.dirname(__file__)
            # 配置文件的路径
            config_path = os.path.join(curdir, "config.json")
            # 创建一个过期字典，有效期为1小时
            self.params_cache = ExpiredDict(60 * 60)
            # 如果配置文件不存在
            if not os.path.exists(config_path):
                # 输出日志信息，配置文件不存在，将使用模板
                logger.info('[RP] 配置文件不存在，将使用config.json.template模板')
                # 模板配置文件的路径
                config_path = os.path.join(curdir, "config.json.template")
            # 打开并读取配置文件
            with open(config_path, "r", encoding="utf-8") as f:
                # 加载 JSON 文件
                config = json.load(f)
                rootdir = os.path.dirname(os.path.dirname(curdir))
                dbdir = os.path.join(rootdir, "db")
                if not os.path.exists(dbdir):
                    os.mkdir(dbdir)
                logger.info("[verify_turbo] inited")
                user_db = os.path.join(dbdir, "user.db")
                self.user_db = sqlite3.connect(user_db, check_same_thread=False)
                # 创建频道对象
                self.comapp, self.type, self.num = create_channel_object()
                # 获取配置文件中的各种参数
                self.api_key = config.get("api_key", "")
                self.domain_name = config["domain_name"]
                self.image_ins = config.get("image_ins", "/p")
                self.blend_ins = config.get("blend_ins", "/b")
                self.change_ins = config.get("change_ins", "/c")
                self.split_url = config.get("split_url", False)
                self.short_url_api = config.get("short_url_api", "")
                self.default_params = config.get("default_params", {"action": "IMAGINE:出图", "prompt": ""})
                self.gpt_optimized = config.get("gpt_optimized", False)
                self.trial_lock = config.get("trial_lock", 3)
                self.lock = config.get("lock", False)
                self.group_lock = config.get("group_lock", False)
                self.local_data = threading.local()
                self.complete_prompt = config.get("complete_prompt", "任务完成！")
                # 创建 MidJourneyModule 对象
                self.mm = MidJourneyModule(api_key=self.api_key, domain_name=self.domain_name)
                # 如果 domain_name 为空或包含"你的域名"，则抛出异常
                if not self.domain_name or "你的域名" in self.domain_name:
                    raise Exception("please set your Midjourney domain_name in config or environment variable.")
            # 设置事件处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            # 输出日志信息，表示插件已初始化
            logger.info("[RP] inited")
        except Exception as e:  # 捕获所有的异常
            if isinstance(e, FileNotFoundError):  # 如果是 FileNotFoundError 异常
                # 输出日志信息，表示配置文件未找到
                logger.warn(f"[RP] init failed, config.json not found.")
            else:  # 如果是其他类型的异常
                # 输出日志信息，表示初始化失败，并附加异常信息
                logger.warn("[RP] init failed." + str(e))
            # 抛出异常，结束程序
            raise e

    # 这个方法是一个事件处理方法，当插件接收到指定类型的事件时，会调用这个方法来处理
    def on_handle_context(self, e_context: EventContext):
        # 如果事件的类型不是图片创建或图片，则直接返回，不进行后续处理
        if e_context['context'].type not in [ContextType.IMAGE_CREATE, ContextType.IMAGE]:
            return
        # 将图片请求内容的日志输出
        logger.info("[RP] image_query={}".format(e_context['context'].content))
        # 创建一个回复对象
        reply = Reply()
        try:
            # 获取会话ID
            user_id = e_context['context']["session_id"]
            # 获取事件内容
            content = e_context['context'].content[:]

            if e_context['context'].type == ContextType.IMAGE_CREATE:
                logger.debug("收到 IMAGE_CREATE 事件.")
                if self.lock:
                    logger.debug("使用限制已开启.")
                    if e_context["context"]["isgroup"]:
                        if self.group_lock:
                            continue_a, continue_b, remaining = self.check_and_update_usage_limit(
                                trial_lock=self.trial_lock,
                                user_id=user_id,
                                db_conn=self.user_db)
                            logger.debug(
                                f"群聊锁已开启. continue_a={continue_a}, continue_b={continue_b}, remaining={remaining}")
                        else:
                            continue_a, continue_b, remaining = True, False, ""
                            logger.debug("群聊锁未开启，直接放行.")
                    else:
                        continue_a, continue_b, remaining = self.check_and_update_usage_limit(
                            trial_lock=self.trial_lock,
                            user_id=user_id,
                            db_conn=self.user_db)
                        logger.debug(
                            f"非群聊上下文. continue_a={continue_a}, continue_b={continue_b}, remaining={remaining}")
                else:
                    continue_a, continue_b, remaining = True, False, ""
                    logger.debug("使用限制未开启.")
            else:
                continue_a, continue_b, remaining = True, False, ""
                logger.debug("收到图像信息，继续执行.")

            if continue_a and continue_b:
                self.local_data.reminder_string = f"\n💳您的绘画试用次数剩余：{remaining}次"
            elif not continue_a and not continue_b:
                reply.type = ReplyType.TEXT
                reply.content = f"⚠️提交失败，您的绘画试用次数剩余：0次 "
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            else:
                self.local_data.reminder_string = remaining

            # 如果事件类型是图片创建
            if e_context['context'].type == ContextType.IMAGE_CREATE:
                # 调用处理图片创建的方法
                self.handle_image_create(e_context, user_id, content, reply)
            # 如果用户ID存在于参数缓存中
            elif user_id in self.params_cache:
                # 调用处理参数缓存的方法
                self.handle_params_cache(e_context, user_id, content, reply)
            # 设置回复内容
            e_context['reply'] = reply
            # 设置事件动作为打断并传递，跳过处理context的默认逻辑
            e_context.action = EventAction.BREAK_PASS
            # 记录日志，事件动作设置为打断并传递，回复已设置
            logger.debug("Event action set to BREAK_PASS, reply set.")
        except Exception as e:  # 捕获异常
            # 设置回复类型为错误
            reply.type = ReplyType.ERROR
            # 设置回复内容为异常信息
            reply.content = "[RP] " + str(e)
            # 设置回复
            e_context['reply'] = reply
            # 记录异常日志
            logger.exception("[RP] exception: %s" % e)
            # 设置事件动作为继续，即使发生异常，也继续进行后续处理
            e_context.action = EventAction.CONTINUE

    def handle_image_create(self, e_context, user_id, content, reply):
        # 使用format_content方法格式化内容
        prompt, commands = format_content(content=content)

        # 深复制default_params到params
        params = {**self.default_params}

        # 处理垫图的情况
        if self.image_ins in prompt:
            # 移除图片插入标记
            prompt = prompt.replace(self.image_ins, "")
            prompt = generate_prompt(content=prompt) if self.gpt_optimized else prompt
            # 将params添加到用户的参数缓存中
            self.params_cache[user_id] = {'image_params': params}

            # 向params中的prompt添加内容
            if params.get("prompt", ""):
                params["prompt"] += f", {prompt}"
            else:
                params["prompt"] += f"{prompt}"

            # 记录日志
            logger.info("[RP] params={}".format(params))

            # 设置回复类型为INFO，内容为提示用户发送图片的消息
            reply.type = ReplyType.INFO
            reply.content = "请发送一张图片给我"

        # 处理合图的情况
        elif self.blend_ins in prompt:
            logger.info("[RP] blend_ins prompt={}".format(prompt))

            try:
                # 从用户的输入中获取需要合成的图片数量
                num_pictures = int(prompt.split()[1])
            except (IndexError, ValueError):
                # 如果出现错误，设置回复类型为ERROR，内容为错误提示
                trigger = conf()['image_create_prefix'][0]
                reply.type = ReplyType.TEXT
                reply.content = f"指令不正确，请根据示例格式重新输入：{trigger} {self.blend_ins} 2\n合图数量仅限2-5张"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                return

            # 检查图片数量是否在2-5张之间
            if not 2 <= num_pictures <= 5:
                trigger = conf()['image_create_prefix'][0]
                reply.type = ReplyType.TEXT
                reply.content = f"指令不正确，请根据示例格式重新输入：{trigger} {self.blend_ins} 2\n合图数量仅限2-5张"
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                return

            # 添加用户的合成参数到params_cache
            self.params_cache[user_id] = {'blend_params': params, 'num_pictures': num_pictures,
                                          'base64_data': []}

            # 记录调试日志
            logger.debug(f"self.params_cache_2:{self.params_cache}")

            # 向params中的prompt添加内容
            if params.get("prompt", ""):
                params["prompt"] += f", {prompt}"
            else:
                params["prompt"] += f"{prompt}"

            # 记录日志
            logger.info("[RP] params={}".format(params))

            # 设置回复类型为INFO，内容为提示用户发送指定数量的图片的消息
            reply.type = ReplyType.INFO
            reply.content = f"请直接发送{num_pictures}张图片给我"
        elif self.change_ins in prompt:  # 处理变换，示例输入：/c V/U 1-4
            # 处理提交的UV值
            submit_uv = ' '.join(prompt.replace(self.change_ins, "").strip().split())
            logger.debug("[RP] submit_uv post_json={}".format(" ".join(submit_uv)))

            # 检查输入的格式是否正确
            pattern = re.compile(r'^\d+\s[VU]\d$')
            if not pattern.match(submit_uv):
                trigger = conf()['image_create_prefix'][0]
                reply.type = ReplyType.ERROR
                reply.content = f"格式不正确。请使用如下示例格式：\n{trigger} {self.change_ins} 8528881058085979 V1"
            else:
                # 解析输入的值
                number, v_value = submit_uv.split()
                logger.debug("Parsed values: Number: {}, V value: {}".format(number, v_value))

                # 确保UV值在U1-U4和V1-V4范围内
                if v_value in ["U1", "U2", "U3", "U4", "V1", "V2", "V3", "V4"]:
                    simple_data = self.mm.get_simple(content=number + " " + v_value)

                    # 发送任务提交消息
                    self.send_task_submission_message(e_context, messageId=simple_data["result"])

                    # 获取图片的URL
                    task_data = self.mm.get_image_url(id=simple_data["result"])
                    if task_data["failReason"] is None:

                        # 生成新的URL
                        new_url = self.generate_new_url(task_data=task_data)

                        # 生成短URL
                        short_url = self.get_short_url(short_url_api=self.short_url_api, url=new_url)

                        # 计算时间差
                        time_diff_start_finish_td, time_diff_submit_finish_td = self.get_time_diff(task_data)

                        logger.debug("new_url: %s" % new_url)

                        # 创建一个新的回复
                        com_reply = self.create_reply(new_url=new_url, data=simple_data)

                        # 发送回复
                        send_with_retry(self.comapp, com_reply, e_context)

                        logger.debug("The comapp object is an instance of: " + type(self.comapp).__name__)
                        reply.type = ReplyType.TEXT

                        # 设置回复内容
                        reply.content = self.complete_prompt.format(id=simple_data["result"],
                                                                    change_ins=self.change_ins, imgurl=short_url,
                                                                    start_finish=time_diff_start_finish_td,
                                                                    submit_finish=time_diff_submit_finish_td)

                        logger.debug("Sent image URL and completed prompt.")
                    else:
                        reply.type = ReplyType.TEXT
                        reply.content = task_data["failReason"]
                        logger.debug("Sent failReason as reply content.")
        else:
            # 如果没有识别到特定的指令，则执行默认的操作，生成一个新的图像
            logger.debug("Generating prompt...")
            prompt = generate_prompt(content=prompt) if self.gpt_optimized else prompt
            prompt += commands
            logger.debug(f"Generated prompt: {prompt}")

            logger.debug("Getting imagination data...")
            imagine_data = self.mm.get_imagine(prompt=prompt)
            if isinstance(imagine_data, str):
                # 如果返回的是错误消息，则直接发送错误消息
                reply.type = ReplyType.TEXT
                reply.content = f"任务提交失败，{imagine_data}"
                logger.error(f"Received error message: {imagine_data}")
            else:
                self.send_task_submission_message(e_context, messageId=imagine_data["result"])
                logger.debug(f"Received imagination data: {imagine_data}")

                time.sleep(10)  # 等待一段时间，以确保任务已经处理完成

                logger.debug("Getting image URL...")
                task_data = self.mm.get_image_url(id=imagine_data["result"])
                logger.debug(f"Received task data: {task_data}")
                if isinstance(task_data, str):
                    # 错误信息响应
                    reply.type = ReplyType.TEXT
                    reply.content = task_data
                    logger.error(f"Received error message: {task_data}")
                else:
                    # 正常的JSON响应
                    if task_data["failReason"] is None:
                        # 处理图片链接
                        new_url = self.generate_new_url(task_data=task_data)
                        # 生成短链接
                        short_url = self.get_short_url(short_url_api=self.short_url_api, url=new_url)
                        # 计算时间差
                        time_diff_start_finish_td, time_diff_submit_finish_td = self.get_time_diff(
                            task_data)

                        logger.debug("new_url: %s" % new_url)

                        com_reply = self.create_reply(new_url=new_url, data=imagine_data)

                        # 发送回复
                        send_with_retry(self.comapp, com_reply, e_context)

                        reply.type = ReplyType.TEXT

                        # 设置回复内容
                        reply.content = self.complete_prompt.format(id=imagine_data["result"],
                                                                    change_ins=self.change_ins,
                                                                    imgurl=short_url,
                                                                    start_finish=time_diff_start_finish_td,
                                                                    submit_finish=time_diff_submit_finish_td)

                        logger.debug("Sent image URL and completed prompt.")
                    else:
                        reply.type = ReplyType.TEXT
                        reply.content = task_data["failReason"]
                        logger.debug("Sent failReason as reply content.")
        # 设置回复内容和动作
        e_context['reply'] = reply
        e_context.action = EventAction.BREAK_PASS  # 事件结束后，跳过处理context的默认逻辑
        logger.debug("Event action set to BREAK_PASS, reply set.")

    def handle_params_cache(self, e_context, user_id, content, reply):
        # 如果参数缓存中存在对应用户的图像参数
        if 'image_params' in self.params_cache[user_id]:
            cmsg = e_context['context']['msg']
            logger.debug("params_cache：%s" % self.params_cache)
            logger.debug("user_id in self.params_cache[user_id]")
            img_params = self.params_cache[user_id]
            del self.params_cache[user_id]  # 删除已使用的参数缓存
            cmsg.prepare()

            # 将用户的输入转换为 base64 编码
            base64_data = convert_base64(content)
            base64_data = 'data:image/png;base64,' + base64_data

            # 使用这些参数生成一个新的图像
            imagine_data = self.mm.get_imagine(prompt=img_params['image_params']["prompt"], base64_data=base64_data)

            if isinstance(imagine_data, str):  # 如果返回错误信息，则直接发送错误信息
                reply.type = ReplyType.TEXT
                reply.content = f"任务提交失败，{imagine_data}"
                logger.error(f"Received error message: {imagine_data}")
            else:
                # 否则，获取新的图像链接，并将其发送给用户
                self.send_task_submission_message(e_context, messageId=imagine_data["result"])
                logger.debug(f"Received imagination data: {imagine_data}")

                time.sleep(10)  # 等待一段时间以确保任务已经处理完成

                logger.debug("Getting image URL...")
                task_data = self.mm.get_image_url(id=imagine_data["result"])
                logger.debug(f"Received task data: {task_data}")
                if isinstance(task_data, str):  # 错误信息响应
                    reply.type = ReplyType.TEXT
                    reply.content = task_data
                    logger.error(f"Received error message: {task_data}")
                else:  # 正常的JSON响应
                    if task_data["failReason"] is None:
                        # 处理图片链接
                        new_url = self.generate_new_url(task_data=task_data)

                        # 生成短链接
                        short_url = self.get_short_url(short_url_api=self.short_url_api, url=new_url)

                        # 计算时间差
                        time_diff_start_finish_td, time_diff_submit_finish_td = self.get_time_diff(task_data)

                        logger.debug("new_url: %s" % new_url)

                        com_reply = self.create_reply(new_url=new_url, data=imagine_data)
                        # 发送回复
                        send_with_retry(self.comapp, com_reply, e_context)

                        reply.type = ReplyType.TEXT

                        # 设置回复内容
                        reply.content = self.complete_prompt.format(id=imagine_data["result"],
                                                                    change_ins=self.change_ins, imgurl=short_url,
                                                                    start_finish=time_diff_start_finish_td,
                                                                    submit_finish=time_diff_submit_finish_td)

                        logger.debug("Sent image URL and completed prompt.")
                    else:
                        reply.type = ReplyType.TEXT
                        reply.content = task_data["failReason"]
                        logger.debug("Sent failReason as reply content.")
        elif 'num_pictures' in self.params_cache[user_id]:
            cmsg = e_context['context']['msg']
            logger.debug("params_cache：%s" % self.params_cache)
            logger.debug("user_id in self.params_cache[user_id]")
            cmsg.prepare()

            # 获取当前用户的图像参数
            img_params = self.params_cache[user_id]

            # 将用户的输入转换为 base64 编码
            base64_data = convert_base64(content)
            base64_data = 'data:image/png;base64,' + base64_data

            # 将新的 base64 数据添加到列表中
            img_params['base64_data'].append(base64_data)

            # 减少待收集的图片数量
            img_params['num_pictures'] -= 1

            # 如果收集到足够数量的图片，调用函数并清除用户数据
            if img_params['num_pictures'] == 0:
                blend_data = self.mm.submit_blend(img_params['base64_data'])
                del self.params_cache[user_id]  # 删除已使用的参数缓存

                if isinstance(blend_data, str):
                    reply.type = ReplyType.TEXT
                    reply.content = f"任务提交失败，{blend_data}"
                    logger.error(f"Received error message: {blend_data}")
                else:
                    # 获取混合后的图像链接，并将其发送给用户
                    self.send_task_submission_message(e_context, messageId=blend_data["result"])
                    logger.debug(f"Received imagination data: {blend_data}")
                    time.sleep(10)  # 等待一段时间以确保任务已经处理完成
                    logger.debug("Getting image URL...")
                    task_data = self.mm.get_image_url(id=blend_data["result"])
                    logger.debug(f"Received task data: {task_data}")

                    if isinstance(task_data, str):
                        # 错误信息响应
                        reply.type = ReplyType.TEXT
                        reply.content = task_data
                        logger.error(f"Received error message: {task_data}")
                    else:
                        # 正常的JSON响应
                        if task_data["failReason"] is None:
                            # 处理图片链接
                            new_url = self.generate_new_url(task_data=task_data)

                            # 生成短链接
                            short_url = self.get_short_url(short_url_api=self.short_url_api, url=new_url)

                            # 计算时间差
                            time_diff_start_finish_td, time_diff_submit_finish_td = self.get_time_diff(
                                task_data)

                            logger.debug("new_url: %s" % new_url)

                            com_reply = self.create_reply(new_url=new_url, data=blend_data)

                            # 发送回复
                            send_with_retry(self.comapp, com_reply, e_context)

                            reply.type = ReplyType.TEXT
                            # 设置回复内容
                            reply.content = self.complete_prompt.format(id=blend_data["result"],
                                                                        change_ins=self.change_ins,
                                                                        imgurl=short_url,
                                                                        start_finish=time_diff_start_finish_td,
                                                                        submit_finish=time_diff_submit_finish_td)
                            logger.debug("Sent image URL and completed prompt.")
                        else:
                            reply.type = ReplyType.TEXT
                            reply.content = task_data["failReason"]
                            logger.debug("Sent failReason as reply content.")

    # 定义一个方法，用于生成帮助文本
    def get_help_text(self, verbose=False, **kwargs):
        # 检查配置中是否启用了画图功能
        if not conf().get('image_create_prefix'):
            return "画图功能未启用"  # 如果未启用，则返回提示信息
        else:
            # 否则，获取触发前缀
            trigger = conf()['image_create_prefix'][0]
        # 初始化帮助文本，说明利用 midjourney api 来画图
        help_text = "\n🔥使用Midjourney来画图，支持垫图、合图、变换等操作\n"
        # 如果不需要详细说明，则直接返回帮助文本
        if not verbose:
            return help_text
        # 否则，添加详细的使用方法到帮助文本中
        help_text += f"使用方法:\n使用\"{trigger}[内容描述]\"的格式作画，如\"{trigger}一个中国漂亮女孩\"\n垫图指令：{trigger} {self.image_ins}，合图指令：{trigger} {self.blend_ins}\n垫图指令后面可以加关键词，合图指令后面不需要加"
        # 返回帮助文本
        return help_text

    def get_short_url(self, short_url_api, url):
        # 检查是否提供了短网址 API
        if short_url_api != "":
            # 发送POST请求到短网址 API，并传入原始网址
            response = requests.post(short_url_api, json={"url": url})
            data = response.json()
            # 构建完整的短网址，将API基本URL与响应中的键值连接起来
            short_url = short_url_api + data["key"]
            return short_url
        else:
            # 如果未提供短网址 API，则返回原始网址
            return url

    def get_time_diff(self, task_data):
        # 将时间戳值转换为秒
        startTime_sec = task_data['startTime'] / 1000
        finishTime_sec = task_data['finishTime'] / 1000 if task_data['finishTime'] is not None else None
        submitTime_sec = task_data['submitTime'] / 1000

        if finishTime_sec is not None:
            # 计算开始时间和结束时间之间的时间差（秒）
            time_diff_start_finish = finishTime_sec - startTime_sec
            # 计算提交时间和结束时间之间的时间差（秒）
            time_diff_submit_finish = finishTime_sec - submitTime_sec

            # 将时间差转换为 timedelta 对象，以便更容易处理
            time_diff_start_finish_td = timedelta(seconds=time_diff_start_finish)
            time_diff_submit_finish_td = timedelta(seconds=time_diff_submit_finish)

            # 获取时间差的总秒数
            time_diff_start_finish_td_sec = time_diff_start_finish_td.total_seconds()
            time_diff_submit_finish_td_sec = time_diff_submit_finish_td.total_seconds()
        else:
            # 如果 finishTime_sec 为 None，则将时间差设置为 None
            time_diff_start_finish_td_sec = None
            time_diff_submit_finish_td_sec = None

        return time_diff_start_finish_td_sec, time_diff_submit_finish_td_sec

    def send_task_submission_message(self, e_context, messageId):
        com_reply = Reply()
        com_reply.type = ReplyType.TEXT
        context = e_context['context']
        if context.kwargs.get('isgroup'):
            msg = context.kwargs.get('msg')
            nickname = msg.actual_user_nickname  # 获取昵称
            com_reply.content = "@{name}\n☑️您的绘图任务提交成功！\n🆔ID：{id}\n⏳正在努力出图，请您耐心等待...".format(
                name=nickname, id=messageId) + self.local_data.reminder_string
        else:
            com_reply.content = "☑️您的绘图任务提交成功！\n🆔ID：{id}\n⏳正在努力出图，请您耐心等待...".format(
                id=messageId) + self.local_data.reminder_string
        self.comapp.send(com_reply, context)

    def check_and_update_usage_limit(self, trial_lock, user_id, db_conn):
        cur = db_conn.cursor()

        # 确保midjourneyturbo表存在
        cur.execute("""
            CREATE TABLE IF NOT EXISTS midjourneyturbo
            (UserID TEXT PRIMARY KEY, TrialCount INTEGER, TrialDate TEXT);
        """)
        db_conn.commit()

        # 从数据库中查询用户
        cur.execute("""
            SELECT TrialCount, TrialDate FROM midjourneyturbo 
            WHERE UserID = ?
        """, (user_id,))
        row = cur.fetchone()

        # 如果用户不存在，插入一个新用户并设置试用次数和日期，然后返回True和试用次数减1
        if row is None:
            trial_count = trial_lock - 1  # 试用次数减1
            cur.execute("""
                INSERT INTO midjourneyturbo (UserID, TrialCount, TrialDate) VALUES (?, ?, ?)
            """, (user_id, trial_count, datetime.date.today().isoformat()))  # 插入用户，并设置当前日期和试用次数
            db_conn.commit()
            return True, True, trial_count

        # 用户存在于数据库中，检查试用次数和日期
        trial_count = row[0] if row and row[0] is not None else trial_lock
        trial_date = row[1] if row and row[1] is not None else None
        today = datetime.date.today().isoformat()

        if trial_count == 0 and trial_date == today:  # 今天的试用次数已经用完
            return False, False, ""

        if trial_count > 0 and trial_date == today:  # 试用次数有剩余，并且日期是今天
            trial_count -= 1  # 减少试用次数
        else:  # 试用次数为0或者日期不是今天
            trial_count = trial_lock - 1  # 重置试用次数并减去1
            trial_date = today  # 更新试用日期

        cur.execute("""
            UPDATE midjourneyturbo 
            SET TrialCount = ?, TrialDate = ?
            WHERE UserID = ?
        """, (trial_count, trial_date, user_id))
        db_conn.commit()
        return True, True, trial_count

    def generate_new_url(self, task_data):
        if self.split_url:
            split_url = task_data["imageUrl"].split('/')
            new_url = '/'.join(split_url[0:3] + split_url[5:])
        else:
            new_url = task_data["imageUrl"]
        return new_url

    def create_reply(self, new_url, data):
        com_reply = Reply()
        com_reply.type = self.type

        if self.num != 1:
            com_reply.content = new_url
        else:
            # 下载并压缩图片
            image_path = download_and_compress_image(new_url, data['result'])
            image_storage = open(image_path, 'rb')
            com_reply.content = image_storage
        return com_reply
