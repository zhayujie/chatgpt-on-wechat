# encoding:utf-8
import base64
import io
import re
import threading
import time

import requests
from PIL import Image

import plugins
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from channel import channel_factory
from channel.chat_message import ChatMessage
from common.expired_dict import ExpiredDict
from plugins import *


@plugins.register(
    name="Midjourney",
    desire_priority=98,
    hidden=False,
    desc="AI drawing plugin of midjourney",
    version="1.0",
    author="baojingyu",
)
class Midjourney(Plugin):
    def __init__(self):
        super().__init__()
        # 获取当前文件的目录
        curdir = os.path.dirname(__file__)
        # 配置文件的路径
        config_path = os.path.join(curdir, "config.json")
        # 如果配置文件不存在
        if not os.path.exists(config_path):
            # 输出日志信息，配置文件不存在，将使用模板
            logger.info('[Midjourney] 配置文件不存在，将使用config.json.template模板')
            # 模板配置文件的路径
            config_path = os.path.join(curdir, "config.json.template")
        # 打开并读取配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            # 加载 JSON 文件
            self.mj_plugin_config = json.load(f)
            # 用户绘图模式
            self.user_drawing_mode = self.mj_plugin_config.get("user_drawing_mode", "relax")
            # 群聊绘图模式
            self.group_drawing_mode = self.mj_plugin_config.get("group_drawing_mode", "relax")
            # 默认绘图模式
            self.default_drawing_mode = self.mj_plugin_config.get("default_drawing_mode", "relax")
            # 使用图像创建前缀，搭配image_create_prefix使用
            self.use_image_create_prefix = self.mj_plugin_config.get("default_drawing_mode", True)
            self.mj_trigger_prefix = self.mj_plugin_config.get("mj_trigger_prefix", "/")
            # 需要搭建Mindjourney Proxy https://github.com/novicezk/midjourney-proxy/blob/main/README_CN.md
            self.mj_proxy_server = self.mj_plugin_config.get("mj_proxy_server")
            self.mj_proxy_api_secret = self.mj_plugin_config.get("mj_proxy_api_secret", "")
            if not self.mj_proxy_server:
                logger.error(
                    f"[Midjourney] Initialization failed, missing required parameters , config={self.mj_plugin_config}")
                # 获取 PluginManager 的单例实例
                plugin_manager = PluginManager()
                # 停用Midjourney
                plugin_manager.disable_plugin("Midjourney")
                return
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.proxy = conf().get("proxy")
        if self.proxy:
            self.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
        else:
            self.proxies = None
        # 根据channel_type 动态创建通道
        self.channel_type = conf().get("channel_type")
        self.channel = channel_factory.create_channel(self.channel_type)
        self.task_id_dict = ExpiredDict(conf().get("expires_in_seconds",60 * 60))
        self.task_msg_dict = ExpiredDict(conf().get("expires_in_seconds",60 * 60))
        self.cmd_dict = ExpiredDict(conf().get("expires_in_seconds",60 * 60))
        # 批量查询任务结果
        self.batch_size = 10
        self.semaphore = threading.Semaphore(1)
        self.lock = threading.Lock()  # 用于控制对sessions的访问
        self.thread = threading.Thread(target=self.background_query_task_result)
        self.thread.start()
        logger.info(f"[Midjourney] inited, config={self.mj_plugin_config}")

    def on_handle_context(self, e_context: EventContext):
        if not self.mj_plugin_config:
            return

        context = e_context['context']
        if context.type not in [ContextType.TEXT, ContextType.IMAGE, ContextType.IMAGE_CREATE]:
            return
        msg: ChatMessage = e_context["context"]["msg"]
        logger.info(f"[Midjourney] context msg={msg}")
        state = ""
        # 检查 msg.other_user_id 和 msg.actual_user_nickname 是否为 None，如果是，则将它们替换为空字符串
        other_user_id = msg.other_user_id if msg.other_user_id else ""
        actual_user_nickname = msg.actual_user_nickname if msg.actual_user_nickname else ""
        if not msg.is_group:
            state = "u:" + other_user_id + ":" + actual_user_nickname
        else:
            state = "r:" + other_user_id + ":" + actual_user_nickname
        # Midjourney 作图任务
        self.process_midjourney_task(state, e_context)

    # imagine 命令：处理图片生成请求，并根据优先级添加模式标识。
    # up 命令：处理任务按钮的操作请求。
    # img2img 命令：处理图像到图像的生成请求。
    # describe 命令：处理图像描述请求。
    # shorten 命令：处理文本缩短请求。
    # seed 命令：获取任务图片的 seed 值。
    # query 命令：查询任务的状态。
    def process_midjourney_task(self, state, e_context: EventContext):
        content = e_context["context"].content
        msg: ChatMessage = e_context["context"]["msg"]
        isgroup = msg.is_group
        result = None
        prompt = ""
        try:
            # 获取配置中的触发前缀和图片生成前缀列表
            image_create_prefixes = conf().get("image_create_prefix", [])

            # 处理图片生成的前缀
            if e_context["context"].type == ContextType.IMAGE_CREATE and self.mj_plugin_config.get(
                    "use_image_create_prefix"):
                # 创建一个正则模式来匹配所有可能的前缀
                prefix_pattern = '|'.join(map(re.escape, image_create_prefixes))
                # 使用正则表达式只在字符串开头匹配前缀并替换
                content = re.sub(f'^(?:{prefix_pattern})', f"{self.mj_trigger_prefix}imagine ", msg.content, count=1)
                logger.debug(f"[Midjourney] ole_content: {msg.content} , new_content: {content}")

            # 处理 imagine 命令
            if content.startswith(f"{self.mj_trigger_prefix}imagine "):
                prompt = content[9:]

                # 检查用户是否已经输入了模式标识
                if not any(flag in prompt for flag in ["--relax", "--fast", "--turbo"]):
                    # 根据优先级添加模式标识
                    if not isgroup and is_valid_mode(self.user_drawing_mode):
                        prompt += f" --{self.user_drawing_mode}"
                    elif isgroup and is_valid_mode(self.group_drawing_mode):
                        prompt += f" --{self.group_drawing_mode}"
                    elif is_valid_mode(self.default_drawing_mode):
                        prompt += f" --{self.default_drawing_mode}"

                # 处理 imagine 请求
                result = self.handle_imagine(prompt, state)

            # 处理 up 命令
            elif content.startswith(f"{self.mj_trigger_prefix}up "):
                arr = content[4:].split()
                try:
                    task_id = arr[0]
                    index = int(arr[1])
                except Exception as e:
                    e_context["reply"] = Reply(ReplyType.TEXT, '❌ 您的任务提交失败\nℹ️ 参数错误')
                    e_context.action = EventAction.BREAK_PASS
                    return

                # 获取任务
                task = self.get_task(task_id)
                if task is None:
                    e_context["reply"] = Reply(ReplyType.TEXT, '❌ 您的任务提交失败\nℹ️ 任务ID不存在')
                    e_context.action = EventAction.BREAK_PASS
                    return

                # 检查按钮序号是否正确
                if index > len(task['buttons']):
                    e_context["reply"] = Reply(ReplyType.TEXT, '❌ 您的任务提交失败\nℹ️ 按钮序号不正确')
                    e_context.action = EventAction.BREAK_PASS
                    return

                # 获取按钮
                button = task['buttons'][index - 1]
                if button['label'] == 'Custom Zoom':
                    e_context["reply"] = Reply(ReplyType.TEXT, '❌ 您的任务提交失败\nℹ️ 暂不支持自定义变焦')
                    e_context.action = EventAction.BREAK_PASS
                    return

                # 发送请求
                result = self.post_json('/submit/action',
                                        {'customId': button['customId'], 'taskId': task_id, 'state': state})
                if result.get("code") == 21:
                    result = self.post_json('/submit/modal',
                                            {'taskId': result.get("result"), 'state': state})

            # 处理 img2img 命令
            elif content.startswith(f"{self.mj_trigger_prefix}img2img "):
                self.cmd_dict[msg.actual_user_id] = content
                e_context["reply"] = Reply(ReplyType.TEXT, '请给我发一张图片作为垫图')
                e_context.action = EventAction.BREAK_PASS
                return

            # 处理 describe 命令
            elif content == f"{self.mj_trigger_prefix}describe":
                self.cmd_dict[msg.actual_user_id] = content
                e_context["reply"] = Reply(ReplyType.TEXT, '请给我发一张图片用于图生文')
                e_context.action = EventAction.BREAK_PASS
                return

            # 处理 shorten 命令
            elif content.startswith(f"{self.mj_trigger_prefix}shorten "):
                result = self.handle_shorten(content[9:], state)

            # 处理 seed 命令
            elif content.startswith(f"{self.mj_trigger_prefix}seed "):
                task_id = content[6:]
                result = self.get_task_image_seed(task_id)
                if result.get("code") == 1:
                    e_context["reply"] = Reply(ReplyType.TEXT, '✅ 获取任务图片seed成功\n📨 任务ID: %s\n🔖 seed值: %s' % (
                        task_id, result.get("result")))
                else:
                    e_context["reply"] = Reply(ReplyType.TEXT, '❌ 获取任务图片seed失败\n📨 任务ID: %s\nℹ️ %s' % (
                        task_id, result.get("description")))
                e_context.action = EventAction.BREAK_PASS
                return

            # 处理图片消息
            elif e_context["context"].type == ContextType.IMAGE:
                cmd = self.cmd_dict.get(msg.actual_user_id)
                if not cmd:
                    return
                msg.prepare()
                self.cmd_dict.pop(msg.actual_user_id)
                if f"{self.mj_trigger_prefix}describe" == cmd:
                    result = self.handle_describe(content, state)
                elif cmd.startswith(f"{self.mj_trigger_prefix}img2img "):
                    result = self.handle_img2img(content, cmd[9:], state)
                else:
                    return

            # 处理 query 命令
            elif content.startswith(f"{self.mj_trigger_prefix}query "):
                arr = content[7:].split()
                try:
                    task_id = arr[0]
                except Exception as e:
                    e_context["reply"] = Reply(ReplyType.TEXT, '❌ 您的任务查询失败\nℹ️ 参数错误')
                    e_context.action = EventAction.BREAK_PASS
                    return
                # 查询任务
                task = self.get_task(task_id)
                if task is None:
                    e_context["reply"] = Reply(ReplyType.TEXT, '❌ 您的任务查询失败\nℹ️ 任务ID不存在')
                    e_context.action = EventAction.BREAK_PASS
                    return
                self.add_task(task_id, msg)
                e_context.action = EventAction.BREAK_PASS
                return
            else:
                return
        except Exception as e:
            logger.exception("[Midjourney] handle failed: %s" % e)
            result = {'code': -9, 'description': '服务异常, 请稍后再试'}

        # 处理请求结果
        code = result.get("code")
        if code == 1:
            task_id = result.get("result")
            self.add_task(task_id, msg)

            # 根据 prompt 中的标识设置模式说明
            mode_description = ""
            if "--relax" in prompt:
                mode_description = "ℹ️ Relax模式任务的等待时间通常为1-10分钟"
            reply_text = f'✅ 您的任务已提交\n🚀 正在快速处理中，请稍后\n📨 任务ID: {task_id}\n{mode_description}'
            e_context["reply"] = Reply(ReplyType.TEXT, reply_text)
        elif code == 22:
            self.add_task(result.get("result"), msg)
            e_context["reply"] = Reply(ReplyType.TEXT, f'✅ 您的任务已提交\n⏰ {result.get("description")}')
        else:
            e_context["reply"] = Reply(ReplyType.TEXT, f'❌ 您的任务提交失败\nℹ️ {result.get("description")}')
        e_context.action = EventAction.BREAK_PASS

    def handle_imagine(self, prompt, state):
        return self.post_json('/submit/imagine', {'prompt': prompt, 'state': state})

    def handle_describe(self, img_data, state):

        base64_str = self.image_file_to_base64(img_data)
        return self.post_json('/submit/describe', {'base64': base64_str, 'state': state})

    def handle_shorten(self, prompt, state):
        return self.post_json('/submit/shorten', {'prompt': prompt, 'state': state})

    def handle_img2img(self, img_data, prompt, state):
        base64_str = self.image_file_to_base64(img_data)
        return self.post_json('/submit/imagine', {'prompt': prompt, 'base64': base64_str, 'state': state})

    def post_json(self, api_path, data):
        return requests.post(url=self.mj_proxy_server + api_path, json=data,
                             headers={'mj-api-secret': self.mj_proxy_api_secret}).json()

    def get_task(self, task_id):
        return requests.get(url=self.mj_proxy_server + '/task/%s/fetch' % task_id,
                            headers={'mj-api-secret': self.mj_proxy_api_secret}).json()

    def get_task_image_seed(self, task_id):
        return requests.get(url=self.mj_proxy_server + '/task/%s/image-seed' % task_id,
                            headers={'mj-api-secret': self.mj_proxy_api_secret}).json()

    def query_tasks_by_ids(self, task_ids):
        return self.post_json('/task/list-by-condition', {'ids': task_ids})

    def add_task(self, task_id, msg):
        # 将任务ID存储到任务ID字典中
        self.task_id_dict[task_id] = 'NOT_START'
        # 将任务ID和消息信息关联存储到 task_msg_dict 字典中
        self.task_msg_dict[task_id] = msg

    def background_query_task_result(self):
        while True:
            with self.lock:
                task_ids = list(self.task_id_dict.keys())

                if task_ids:
                    num_batches = (len(task_ids) + self.batch_size - 1) // self.batch_size  # 计算批次数量
                    logger.debug("[Midjourney] background query task result running, size [%s]", len(task_ids))
                    for i in range(num_batches):
                        # 获取当前批次的任务ID列表
                        batch = task_ids[i * self.batch_size:(i + 1) * self.batch_size]

                        self.handle_task_batch(batch)

                        # 等待所有任务处理完成
                        for _ in batch:
                            self.semaphore.acquire()

            # 避免过度占用CPU资源，适当休眠
            time.sleep(0.5)

    def handle_task_batch(self, task_ids):
        tasks = self.query_tasks_by_ids(task_ids)  # 批量查询任务
        if tasks is not None and len(tasks) > 0:
            logger.debug(
                f"[Midjourney] background handle task batch running, size {len(task_ids)}, taskIds [{','.join(task_ids)}]", )
            # 将 tasks 转换成键值对结构
            tasks_map = {task['id']: task for task in tasks}
            for task_id in task_ids:
                task = tasks_map.get(task_id)
                self.process_task(task, task_id)
        else:
            # 如果没有返回任务，释放所有的信号量
            for _ in task_ids:
                self.semaphore.release()

    def process_task(self, task, task_id):
        if task is None:
            self.handle_not_exist_task(task, task_id)
        else:
            self.handle_exist_task(task, task_id)

        # 只在这里释放批处理信号量
        self.semaphore.release()

    def handle_exist_task(self, task, task_id):
        context = Context()
        # 获取当前任务ID对应的消息信息
        msg = self.task_msg_dict.get(task_id)
        # 在已有的context中存储消息信息
        context.kwargs['msg'] = msg
        context.__setitem__("msg", msg)
        state = task.get("state",None)
        if state is None:
            # 检查 msg.other_user_id 和 msg.actual_user_nickname 是否为 None，如果是，则将它们替换为空字符串
            other_user_id = msg.other_user_id if msg.other_user_id else ""
            actual_user_nickname = msg.actual_user_nickname if msg.actual_user_nickname else ""
            if not msg.is_group:
                state = "u:" + other_user_id + ":" + actual_user_nickname
            else:
                state = "r:" + other_user_id + ":" + actual_user_nickname

        state_array = state.split(':', 2)
        reply_prefix = self.extract_state_info(state_array)
        context.__setitem__("receiver", reply_prefix)


        reply = self.generate_reply(task_id, task, context, reply_prefix)
        if reply is not None:
            self.channel.send(reply, context)
        else:
            logger.debug(
                f"[Midjourney] handle task_id: {task_id} , status :{task['status']} , progress : {task['progress']}")

    def handle_not_exist_task(self, task, task_id):
        context = Context()
        msg = self.task_msg_dict.get(task_id)
        context.kwargs['msg'] = msg
        context.__setitem__("msg", msg)

        state = task.get("state",None)
        if state is None:
            # 检查 msg.other_user_id 和 msg.actual_user_nickname 是否为 None，如果是，则将它们替换为空字符串
            other_user_id = msg.other_user_id if msg.other_user_id else ""
            actual_user_nickname = msg.actual_user_nickname if msg.actual_user_nickname else ""
            if not msg.is_group:
                state = "u:" + other_user_id + ":" + actual_user_nickname
            else:
                state = "r:" + other_user_id + ":" + actual_user_nickname
        state_array = state.split(':', 2)
        reply_prefix = self.extract_state_info(state_array)
        context.__setitem__("receiver", reply_prefix)

        reply = Reply(ReplyType.TEXT, '❌ 您的任务执行失败\nℹ️ 任务ID不存在\n📨 任务ID: %s' % (task_id))

        self.channel.send(reply, context)

        logger.debug("[Midjourney] 任务执行失败 , 任务ID不存在: " + task_id)
        self.task_id_dict.pop(task_id)
        self.task_msg_dict.pop(task_id)

    def extract_state_info(self, state_array=None):
        if not state_array:
            receiver = state_array[1] if len(state_array) > 1 else None
            reply_prefix = '@%s ' % state_array[2] if state_array[0] == 'r' else ''
            return reply_prefix
        return ""

    def generate_reply(self, task_id, task, context:Context, reply_prefix=''):
        status = task['status']
        action = task['action']
        description = task.get('description', 'No description available')
        context.__setitem__("promptEn", task['promptEn'])
        if status == 'SUCCESS':
            logger.debug("[Midjourney] 任务已完成: " + task_id)
            self.task_id_dict.pop(task_id)
            self.task_msg_dict.pop(task_id)
            image_url = task.get('imageUrl', None)

            context.__setitem__("description", description)
            context.__setitem__("image_url", image_url)
            if action == 'DESCRIBE' or action == 'SHORTEN':
                prompt = task['properties']['finalPrompt']
                reply_text = f"✅ 任务已完成\n📨 任务ID: {task_id}\n✨ {description}\n\n{self.get_buttons(task)}\n💡 使用 {self.mj_trigger_prefix}up 任务ID 序号执行动作\n🔖 {self.mj_trigger_prefix}up {task_id} 1"
                return Reply(ReplyType.TEXT, reply_text)
            elif action == 'UPSCALE':
                reply_text = f"✅ 任务已完成\n📨 任务ID: {task_id}\n✨ {description}\n\n{self.get_buttons(task)}\n💡 使用 {self.mj_trigger_prefix}up 任务ID 序号执行动作\n🔖 {self.mj_trigger_prefix}up {task_id} 1"
                return Reply(ReplyType.TEXT, reply_text)
            else:
                # image_storage = self.download_and_compress_image(image_url)
                reply_text = f"✅ 任务已完成\n📨 任务ID: {task_id}\n✨ {description}\n\n{self.get_buttons(task)}\n💡 使用 {self.mj_trigger_prefix}up 任务ID 序号执行动作\n🔖 {self.mj_trigger_prefix}up {task_id} 1"
                return Reply(ReplyType.TEXT, reply_text)
        elif status == 'FAILURE':
            self.task_id_dict.pop(task_id)
            self.task_msg_dict.pop(task_id)
            reply_text = f'❌ 任务执行失败\n📨 任务ID: {task_id}\n📒 失败原因: {task["failReason"]}\n✨ {description}'
            return Reply(ReplyType.TEXT, reply_text)

    def image_file_to_base64(self, file_path):
        with open(file_path, "rb") as image_file:
            img_data = image_file.read()
        img_base64 = base64.b64encode(img_data).decode("utf-8")
        os.remove(file_path)
        return "data:image/png;base64," + img_base64

    def get_buttons(self, task):
        res = ''
        index = 1
        for button in task['buttons']:
            name = button['emoji'] + button['label']
            if name in ['🎉Imagine all', '❤️']:
                continue
            res += ' %d - %s\n' % (index, name)
            index += 1
        return res

    def download_and_compress_image(self, img_url, max_size=(800, 800)):  # 下载并压缩图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }
        # 设置代理
        # self.proxies
        # , proxies=self.proxies
        pic_res = requests.get(img_url, headers=headers, stream=True, timeout=60 * 5)
        image_storage = io.BytesIO()
        size = 0
        for block in pic_res.iter_content(1024):
            size += len(block)
            image_storage.write(block)
        image_storage.seek(0)
        logger.debug(f"[MJ] download image success, size={size}, img_url={img_url}")
        # 压缩图片
        initial_image = Image.open(image_storage)
        initial_image.thumbnail(max_size)
        output = io.BytesIO()
        initial_image.save(output, format=initial_image.format)
        output.seek(0)
        return output

    # 检查模式是否有效

    def get_help_text(self, verbose=False, **kwargs):
        help_text = "这是一个能调用midjourney实现ai绘图的扩展能力。\n"
        if not verbose:
            return help_text
        help_text += "使用说明: \n"
        help_text += f"{self.mj_trigger_prefix}imagine 根据给出的提示词绘画;\n"
        help_text += f"{self.mj_trigger_prefix}img2img 根据提示词+垫图生成图;\n"
        help_text += f"{self.mj_trigger_prefix}up 任务ID 序号执行动作;\n"
        help_text += f"{self.mj_trigger_prefix}describe 图片转文字;\n"
        help_text += f"{self.mj_trigger_prefix}shorten 提示词分析;\n"
        help_text += f"{self.mj_trigger_prefix}seed 获取任务图片的seed值;\n"
        help_text += f"{self.mj_trigger_prefix}query 任务ID 查询任务进度;\n"
        help_text += f"默认使用🐢 Relax绘图，也可以在提示词末尾使用 `--relax` 或 `--fast` 参数运行单个作业;\n"
        image_create_prefixes = conf().get("image_create_prefix", [])
        if image_create_prefixes and self.mj_plugin_config.get("use_image_create_prefix",False):
            prefixes = ", ".join(image_create_prefixes)
            help_text += f"支持图片回复前缀关键字：{prefixes}。\n使用格式：{image_create_prefixes[0]}一棵装饰着金色雪花和金色饰品的圣诞树，周围是地板上的礼物。房间是白色的，有浅色木材的装饰，一侧有一个壁炉，大窗户望向户外花园。一颗星星挂在高约三米的绿色松树顶上。这是一个充满节日庆祝气氛的优雅场景，充满了温暖和欢乐。一张超逼真的照片，以高分辨率2000万像素相机的风格拍摄。\n"
        return help_text

def is_valid_mode(mode):
    return mode in ["relax", "fast", "turbo"]
