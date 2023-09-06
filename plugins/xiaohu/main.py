# encoding:utf-8
from datetime import datetime

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from plugins import *
from plugins.xiaohu.functions import FunctionCall
from plugins.xiaohu.functions.google_fns import search_by_google
# from plugins.xiaohu.util.xf_api import XFOCR
from plugins.xiaohu.util.yinshua import OCR_Word

@plugins.register(
    name="Xiaohu",
    desire_priority=-1,
    hidden=True,
    desc="A simple plugin ",
    version="0.1",
    author="lanvent",
)
# def create_channel_object():
#     channel_type = conf().get("channel_type")
#     if channel_type == 'wework':
#         from channel.wework.wework_channel import WeworkChannel
#         return WeworkChannel()
#     elif channel_type == 'ntchat':
#         from channel.wechatnt.ntchat_channel import NtchatChannel
#         return NtchatChannel()
#     elif channel_type == 'weworktop':
#         from channel.weworktop.weworktop_channel import WeworkTopChannel
#         return WeworkTopChannel()
#     else:
#         from channel.wechatnt.ntchat_channel import NtchatChannel
#         return NtchatChannel()

class Xiaohu(Plugin):
    def __init__(self):
        super().__init__()

        # self.comapp = create_channel_object()

        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.ocr = None
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        conf = None
        if not os.path.exists(config_path):
            logger.debug(f"[Xiaohu]不存在配置文件{config_path}")
            conf = {"keyword": {}}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(conf, f, indent=4)
        else:
            logger.debug(f"[Xiaohu]加载配置文件{config_path}")
            with open(config_path, "r", encoding="utf-8") as f:
                conf = json.load(f)
        # 加载关键词
        self.conf = conf

        self.fc = FunctionCall() if self.conf["function_call"] else None
        xfconf = self.conf["XfOcr"]
        ocr_conf = self.conf["OCR_YinShua"]
        self.ocr = OCR_Word(url=ocr_conf['URL'],APPID=ocr_conf['APPID'],API_KEY=ocr_conf['API_KEY'])
        self.prompt = self.conf["prompt"]
        logger.info("[Xiaohu] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT,
            ContextType.IMAGE,
            ContextType.FILE,
            ContextType.JOIN_GROUP,
            ContextType.PATPAT,
        ]:
            return
        if e_context["context"].type == ContextType.FILE:
            return
        if e_context["context"].type == ContextType.IMAGE:
            e_context["context"].type = ContextType.TEXT
            result = self.ocr.main(e_context["context"].content)
            print(result)
            if result == -1:
                e_context["context"].content = "识别失败"
                e_context.action = EventAction.BREAK_PASS  # 事件继续，交付给下个插件或默认逻辑
            else:
                e_context["context"].content = "我通过ocr技术识别出的一些信息，可能有些混乱，请你先理解我的题目后重新调整我的输入内容后输出调整后的问题或题目，并且根据该问题进行解答，我的输入是："+result
                e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑

            return
        if e_context["context"].type == ContextType.JOIN_GROUP:
            e_context["context"].type = ContextType.TEXT
            msg: ChatMessage = e_context["context"]["msg"]
            e_context["context"].content = f'请你随机使用一种说话风格说一句与众不同的问候语来欢迎新用户"{msg.actual_user_nickname}"加入了"{msg.other_user_nickname}"群聊，并告知新用户“群聊内禁止打广告、引流和讨论违法违纪的敏感话题以及仅允许对bot进行轻度使用测试”，不用说你使用了什么风格，直接回复内容就行，除了欢迎内容不要说任何多余的话语。'
            e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
            return

        if e_context["context"].type == ContextType.PATPAT:
            e_context["context"].type = ContextType.TEXT
            msg: ChatMessage = e_context["context"]["msg"]
            if e_context["context"]["isgroup"]:
                e_context["context"].content = f'请你随机使用一种风格和与众不同的玩笑跟"{msg.actual_user_nickname}"说为什么要拍你的服务器，不用说你使用了什么风格，直接发送玩笑内容开玩笑就行，除了玩笑内容不要说任何多余的话语。'
            else:
                e_context["context"].content = f'请你随机使用一种风格和与众不同的玩笑跟"{msg.from_user_nickname}"说为什么要拍你的服务器，不用说你使用了什么风格，直接发送玩笑内容开玩笑就行，除了玩笑内容不要说任何多余的话语。'
            e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
            return
        if e_context["context"].type == ContextType.TEXT:
            content = e_context["context"].content
            logger.debug("[XiaoHu] on_handle_context. content: %s" % content)
            function_response = None
            if content.startswith("搜索") or content.startswith("查一下"):
                # 搜索功能
                com_reply = Reply()
                com_reply.type = ReplyType.TEXT
                context = e_context['context']
                if context.kwargs.get('isgroup'):
                    msg = context.kwargs.get('msg')  # 这是WechatMessage实例
                    nickname = msg.actual_user_nickname  # 获取nickname
                    com_reply.content = "@{name}\n☑️正在给您实时联网必应搜索\n⏳整理深度数据需要时间，请耐心等待...".format(
                        name=nickname)
                else:
                    com_reply.content = "☑️正在给您实时联网必应搜索\n⏳整理深度数据需要时间，请耐心等待..."
                # if self.comapp is not None:
                #     self.comapp.send(com_reply, e_context['context'])
                function_response = search_by_google(content)
                function_response = json.dumps(function_response, ensure_ascii=False)
                logger.debug(f"Function response: {function_response}")  # 打印函数响应
            if function_response is not None:

                msg: ChatMessage = e_context["context"]["msg"]
                current_date = datetime.now().strftime("%Y年%m月%d日%H时%M分")
                if e_context["context"]["isgroup"]:
                    prompt = self.prompt.format(time=current_date, bot_name=msg.to_user_nickname,
                                                name=msg.actual_user_nickname, content=content,
                                                function_response=function_response)
                else:
                    prompt = self.prompt.format(time=current_date, bot_name=msg.to_user_nickname,
                                                name=msg.from_user_nickname, content=content,
                                                function_response=function_response)
                logger.debug(f"prompt :" + prompt)
                logger.debug("messages: %s", [{"role": "system", "content": prompt}])
                e_context["context"].content = prompt
                e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
            else:
                e_context.action = EventAction.BREAK
        #     if content == "test1":
        #
        #         print(e_context["context"].content)
        #         reply = Reply()
        #         reply.type = ReplyType.VOICE
        #
        #         reply.content = r"C:\Users\BY\Documents\GitHub\chatgpt-on-wechat1\tmp\reply-1693016121-652683595.mp3"
        #         e_context["reply"] = reply
        #         e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
        # #
        # if content == "Hello":
        #     reply = Reply()
        #     reply.type = ReplyType.TEXT
        #     msg: ChatMessage = e_context["context"]["msg"]
        #     if e_context["context"]["isgroup"]:
        #         reply.content = f"Hello, {msg.actual_user_nickname} from {msg.from_user_nickname}"
        #     else:
        #         reply.content = f"Hello, {msg.from_user_nickname}"
        #     e_context["reply"] = reply
        #     e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        # if content == "Hi":
        #     reply = Reply()
        #     reply.type = ReplyType.FILE
        #     reply.content = "Hi"
        #     e_context["reply"] = reply
        #     e_context.action = EventAction.BREAK_PASS  # 事件结束，进入默认处理逻辑，一般会覆写reply

        # if content == "End":
        #     # 如果是文本消息"End"，将请求转换成"IMAGE_CREATE"，并将content设置为"The World"
        #     e_context["context"].type = ContextType.IMAGE_CREATE
        #     content = "The World"
        #     e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "输入Hello，我会回复你的名字\n输入End，我会回复你世界的图片\n"
        return help_text
