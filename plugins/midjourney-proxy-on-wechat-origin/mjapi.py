import time
import json
import requests
from common.log import logger


class _mjApi:
    def __init__(self, config):
        self.headers = {
            "Content-Type": "application/json",
        }
        self.proxy = config['discordapp_proxy']
        self.baseUrl = config['mj_url']
        self.headers["mj-api-secret"] = config['mj_api_secret']
        self.imagine_prefix = config['imagine_prefix']
        self.fetch_prefix = config['fetch_prefix']
        self.up_prefix = config['up_prefix']
        self.pad_prefix = config['pad_prefix']
        self.blend_prefix = config['blend_prefix']
        self.describe_prefix = config['describe_prefix']
        self.queue_prefix = config['queue_prefix']
        self.end_prefix = config['end_prefix']

    def set_user(self, user):
        self.user = user

    def set_mj(self, mj_url, mj_api_secret="", proxy=""):
        self.baseUrl = mj_url
        self.proxy = proxy
        self.headers["mj-api-secret"] = mj_api_secret

    def subTip(self, res):
        rj = res.json()
        if not rj:
            return False, "❌ MJ服务异常", ""
        code = rj["code"]
        id = rj['result']
        if code == 1:
            msg = "✅ 您的任务已提交\n"
            msg += f"🚀 正在快速处理中，请稍后\n"
            msg += f"📨 ID: {id}\n"
            msg += f"✍️ 使用[{self.fetch_prefix[0]} + 任务ID操作]\n"
            msg += f"✍️ {self.fetch_prefix[0]} {id}"
            return True, msg, rj["result"]
        else:
            return False, rj['description'], ""

    # 图片想象接口
    def imagine(self, prompt, base64Array=[]):
        try:
            url = self.baseUrl + "/mj/submit/imagine"
            data = {
                "prompt": prompt,
                "base64Array": base64Array
            }
            if self.user:
                data["state"] = self.user
            res = requests.post(url, json=data, headers=self.headers)
            return self.subTip(res)
        except Exception as e:
            logger.exception(e)
            return False, "❌ 任务提交失败", None

    # 放大/变换图片接口
    def simpleChange(self, content):
        try:
            url = self.baseUrl + "/mj/submit/simple-change"
            data = {"content": content}
            if self.user:
                data["state"] = self.user
            res = requests.post(url, json=data, headers=self.headers)
            return self.subTip(res)
        except Exception as e:
            logger.exception(e)
            return False, "❌ 任务提交失败", None

    def reroll(self, taskId):
        try:
            url = self.baseUrl + "/mj/submit/change"
            data = {
                "taskId": taskId,
                "action": "REROLL"
            }
            if self.user:
                data["state"] = self.user
            res = requests.post(url, json=data, headers=self.headers)
            return self.subTip(res)
        except Exception as e:
            logger.exception(e)
            return False, "❌ 任务提交失败", None

    # 混合图片接口
    def blend(self, base64Array, dimensions=""):
        try:
            url = self.baseUrl + "/mj/submit/blend"
            data = {
                "base64Array": base64Array
            }
            if dimensions:
                data["dimensions"] = dimensions
            if self.user:
                data["state"] = self.user
            res = requests.post(url, json=data, headers=self.headers)
            return self.subTip(res)
        except Exception as e:
            logger.exception(e)
            return False, "❌ 任务提交失败", None

    # 识图接口
    def describe(self, base64):
        try:
            url = self.baseUrl + "/mj/submit/describe"
            data = {"base64": base64}
            if self.user:
                data["state"] = self.user
            res = requests.post(url, json=data, headers=self.headers)
            return self.subTip(res)
        except Exception as e:
            logger.exception(e)
            return False, "❌ 任务提交失败", None

    # 查询提交的任务信息
    def fetch(self, id):
        try:
            url = self.baseUrl + f"/mj/task/{id}/fetch"
            res = requests.get(url, headers=self.headers)
            rj = res.json()
            if not rj:
                return False, "❌ 查询任务不存在", None
            user = None
            ruser = None
            if self.user:
                user = json.loads(self.user)
            if rj['state']:
                ruser = json.loads(rj['state'])
            if user and ruser:
                if user['user_id'] != ruser['user_id']:
                    return False, "❌ 该任务不属于您提交，您无权查看", None
            status = rj['status']
            startTime = ""
            finishTime = ""
            imageUrl = ""
            timeup = 0
            if rj['startTime']:
                startTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rj['startTime']/1000))
            if rj['finishTime']:
                finishTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rj['finishTime']/1000))
                timeup = (rj['finishTime'] - rj['startTime'])/1000
            msg = "✅ 查询成功\n"
            msg += f"-----------------------------\n"
            msg += f"📨 ID: {rj['id']}\n"
            msg += f"🚀 进度：{rj['progress']}\n"
            msg += f"⌛ 状态：{self.status(status)}\n"
            if rj['finishTime']:
                msg += f"⏱ 耗时：{timeup}秒\n"
            if rj["action"] == "DESCRIBE":
                msg += f"✨ 描述：{rj['prompt']}\n"
            else:
                msg += f"✨ 描述：{rj['description']}\n"
            if ruser and ruser["user_nickname"]:
                msg += f"🙋‍♂️ 提交人：{ruser['user_nickname']}\n"
            if rj['failReason']:
                msg += f"❌ 失败原因：{rj['failReason']}\n"
            if rj['imageUrl']:
                imageUrl = self.get_img_url(rj['imageUrl'])
                msg += f"🎬 图片地址: {imageUrl}\n"
            if startTime:
                msg += f"⏱ 开始时间：{startTime}\n"
            if finishTime:
                msg += f"⏱ 完成时间：{finishTime}\n"
            msg += f"-----------------------------"
            return True, msg, imageUrl
        except Exception as e:
            logger.exception(e)
            return False, "❌ 查询失败", None

    # 轮询获取任务结果
    def get_f_img(self, id):
        try:
            url = self.baseUrl + f"/mj/task/{id}/fetch"
            status = ""
            rj = ""
            while status != "SUCCESS" and status != "FAILURE":
                time.sleep(3)
                res = requests.get(url, headers=self.headers)
                rj = res.json()
                status = rj["status"]
            if not rj:
                return False, "❌ 任务提交异常", None
            if status == "SUCCESS":
                msg = ""
                startTime = ""
                finishTime = ""
                imageUrl = ""
                action = rj["action"]
                ruser = None
                timeup = 0
                if rj['state']:
                    ruser = json.loads(rj['state'])
                msg += f"-----------------------------\n"
                if rj['finishTime']:
                    timeup = (rj['finishTime'] - rj['startTime'])/1000
                if action == "IMAGINE":
                    msg += f"🎨 绘图成功\n"
                elif  action == "UPSCALE":
                    msg += "🎨 放大成功\n"
                elif action == "VARIATION":
                    msg += "🎨 变换成功\n"
                elif action == "DESCRIBE":
                    msg += "🎨 转述成功\n"
                elif action == "BLEND":
                    msg += "🎨 混合绘制成功\n"
                elif action == "REROLL":
                    msg += "🎨 重新绘制成功\n"
                msg += f"📨 ID: {id}\n"
                if action == "DESCRIBE":
                    msg += f"✨ 描述：{rj['prompt']}\n"
                else:
                    msg += f"✨ 描述：{rj['description']}\n"
                if rj['finishTime']:
                    msg += f"⏱ 耗时：{timeup}秒\n"
                if action == "IMAGINE" or action == "BLEND" or action == "REROLL":
                    msg += f"🪄 放大 U1～U4，变换 V1～V4：使用[{self.up_prefix[0]} + 任务ID]\n"
                    msg += f"✍️ 例如：{self.up_prefix[0]} {id} U1\n"
                if ruser and ruser["user_nickname"]:
                    msg += f"🙋‍♂️ 提交人：{ruser['user_nickname']}\n"
                if rj['imageUrl']:
                    imageUrl = self.get_img_url(rj['imageUrl'])
                    msg += f"🎬 图片地址: {imageUrl}\n"
                if rj['startTime']:
                    startTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rj['startTime']/1000))
                    msg += f"⏱ 开始时间：{startTime}\n"
                if rj['finishTime']:
                    finishTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rj['finishTime']/1000))
                    msg += f"⏱ 完成时间：{finishTime}\n"
                msg += f"-----------------------------"
                return True, msg, imageUrl
            elif status == "FAILURE":
                failReason = rj["failReason"]
                return False, f"❌ 请求失败：{failReason}", ""
            else:
                return False, f"❌ 请求失败：服务异常", ""
        except Exception as e:
            logger.exception(e)
            return False, "❌ 请求失败", ""

    # 查询任务队列
    def task_queue(self):
        try:
            url = self.baseUrl + f"/mj/task/queue"
            res = requests.get(url, headers=self.headers)
            rj = res.json()
            msg = f"✅ 查询成功\n"
            if not rj:
                msg += "❌ 暂无执行中的任务"
                return True, msg
            user = None
            ruser = None
            if self.user:
                user = json.loads(self.user)
            for i in range(0, len(rj)):
                if rj[i]['state']:
                    ruser = json.loads(rj[i]['state'])
                if (ruser and user and user['user_id'] == ruser['user_id']) or not ruser:
                    msg += f"-----------------------------\n"
                    msg += f"📨 ID: {rj[i]['id']}\n"
                    msg += f"🚀 进度：{rj[i]['progress']}\n"
                    msg += f"⌛ 状态：{self.status(rj[i]['status'])}\n"
                    msg += f"✨ 描述：{rj[i]['description']}\n"
                    if ruser and ruser["user_nickname"]:
                        msg += f"🙋‍♂️ 提交人：{ruser['user_nickname']}\n"
                    if rj[i]['failReason']:
                        msg += f"❌ 失败原因：{rj[i]['failReason']}\n"
                    if rj[i]['imageUrl']:
                        imageUrl = self.get_img_url(rj[i]['imageUrl'])
                        msg += f"🎬 图片地址: {imageUrl}\n"
                    startTime = ""
                    if rj[i]['startTime']:
                        startTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rj[i]['startTime']/1000))
                    if startTime:
                        msg += f"⏱开始时间：{startTime}\n"
            msg += f"-----------------------------\n"
            msg += f"共计：{len(rj)}个任务在执行"
            return True, msg
        except Exception as e:
            logger.exception(e)
            return False, "❌ 查询失败"

    def status(self, status):
        msg = ""
        if status == "SUCCESS":
            msg = "已完成"
        elif status == "FAILURE":
            msg = "失败"
        elif status == "SUBMITTED":
            msg = "已提交"
        elif status == "IN_PROGRESS":
            msg = "处理中"
        else:
            msg = "未知"
        return msg

    def get_img_url(self, image_url):
        if self.proxy and image_url.startswith("https://cdn.discordapp.com"):
            image_url = image_url.replace("https://cdn.discordapp.com", self.proxy)
        return image_url

    def help_text(self):
        help_text = "欢迎使用MJ绘画机器人\n"
        help_text += f"这是一个AI绘画工具,只要输入想到的文字,通过人工智能产出相对应的图.\n"
        help_text += f"-----------------------------\n"
        help_text += f"🎨 插件使用说明:\n"
        help_text += f"(1) imagine想象:输入['{self.imagine_prefix[0]} + prompt描述']\n"
        help_text += f"(2) imagine垫图:发送['{self.pad_prefix[0]} + prompt描述']，然后发送多张图片最后发送['{self.end_prefix[0]}']进行垫图（此方法不限群聊还是私聊方式）\n"
        help_text += f"(3) 图片放大和变换:使用['{self.up_prefix[0]} + 任务ID操作']即可放大和变换imagine生成的图片\n"
        help_text += f"(4) describe识图:在私信窗口直接发送图片即可帮你识别解析prompt描述,或发送['{self.describe_prefix[0]}']+图片(此方法不限聊天方式)亦可\n"
        help_text += f"(5) blend混图:发送['{self.blend_prefix[0]}']指令，然后发送多张图片最后发送['{self.end_prefix[0]}']进行混合（此方法不限群聊还是私聊方式）\n"
        help_text += f"(6) 任务查询:使用['{self.fetch_prefix[0]} + 任务ID操作']即可查询所提交的任务\n"
        help_text += f"(7) 任务队列:使用['{self.queue_prefix[0]}']即可查询正在执行中的任务队列\n"
        help_text += f"(8) reroll重新生成:使用['{self.reroll_prefix[0]}' + 任务ID操作]即可重新绘制图片\n"
        help_text += f"-----------------------------\n"
        help_text += f"📕 prompt附加参数 \n"
        help_text += f"1.解释: 在prompt后携带的参数, 可以使你的绘画更别具一格\n"
        help_text += f"2.示例: {self.imagine_prefix[0]} prompt --ar 16:9\n"
        help_text += f"3.使用: 需要使用--key value, key和value空格隔开, 多个附加参数空格隔开\n"
        help_text += f"-----------------------------\n"
        help_text += f"📗 附加参数列表\n"
        help_text += f"1. --v 版本 1,2,3,4,5,5.1,5.2 默认5.2, 不可与niji同用\n"
        help_text += f"2. --niji 动漫风 4或5 默认4, 不可与v同用\n"
        help_text += f"3. --style raw 原始风格, 默认开启,(4a,4b,4c)v4可用\n"
        help_text += f"4. --niji 5模式下--style的值可为[cute:可爱风格;scenic:偏风景风格;original:原始风格;expressive:更精致图文并茂的感觉]\n"
        help_text += f"5. --s 风格化 1-1000 (625-60000)v3\n"
        help_text += f"6. --ar 图像宽高比横纵比 n:n 默认1:1\n"
        help_text += f"7. --chaos 随机性 0-100,值越低越准确\n"
        help_text += f"8. --iw 设置图片提示的权重默认为1,可设为0-2\n"
        help_text += f"9. --no 负面提示（--no plants 会尝试从图像中删除植物）\n"
        help_text += f"10. --q 清晰度 .25 .5 1 2 分别代表: 一般,清晰,高清,超高清,默认1\n"
        help_text += f"11. --weird 0-3000 使用实验参数探索非常规美学。此参数为生成的图像引入了古怪和另类的品质，从而产生独特且意想不到的结果\n"
        help_text += f"-----------------------------\n"
        help_text += f"其他参数可前往文档查看:https://docs.midjourney.com/docs/parameter-list"
        return help_text
