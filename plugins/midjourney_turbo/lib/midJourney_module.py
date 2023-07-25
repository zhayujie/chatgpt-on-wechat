import json
import time
import requests

from common.log import logger


class MidJourneyModule:
    # 初始化函数，需要API密钥和域名作为参数
    def __init__(self, api_key, domain_name):
        self.api_key = api_key
        self.domain_name = domain_name

    # 提交出图或垫图任务的函数
    def get_imagine(self, prompt, base64_data=None):
        """
        提交出图或垫图任务

        参数:
            prompt (str): 提示文本
            base64_data (str): 图像的base64编码数据 (可选)

        返回:
            如果任务提交成功，则返回任务结果数据，否则返回错误描述
        """
        data = {"base64": base64_data, "prompt": prompt}
        api_url = f"{self.domain_name}/mj/submit/imagine"

        headers = {
            "mj-api-secret": self.api_key
        }

        # 发送POST请求
        try:
            response = requests.post(url=api_url, headers=headers, json=data, timeout=120.05)
            if response.status_code == 200:
                get_imagine_data = response.json()
                logger.debug("get_imagine_data: %s" % get_imagine_data)
                if get_imagine_data.get('code') != 1:
                    return get_imagine_data.get('description')
                else:
                    return get_imagine_data
            else:
                logger.error("Error occurred: %s" % response.text)
                return "哦豁，出现了未知错误，请联系管理员~~~"
        except Exception as e:
            logger.error("Error occurred: %s" % str(e))
            return "哦豁，出现了未知错误，请联系管理员~~~"

    # 查询任务获取进度的函数
    def get_image_url(self, id):
        """
        查询任务获取进度

        参数:
            id (str): 任务ID

        返回:
            如果任务成功完成，则返回任务结果数据，否则返回错误描述
        """
        api_url = f"{self.domain_name}/mj/task/{id}/fetch"
        headers = {
            "mj-api-secret": self.api_key
        }

        start_time = time.time()  # 记录开始时间
        while True:
            try:
                # 发送GET请求
                response = requests.get(url=api_url, headers=headers, timeout=120.05)
                if response.status_code == 200:
                    get_image_url_data = response.json()
                    logger.debug("get_image_url_data: %s" % get_image_url_data)
                    if get_image_url_data['failReason'] is None:
                        if get_image_url_data['status'] != 'SUCCESS':
                            time.sleep(30)
                            if time.time() - start_time > 300:
                                return "请求超时，请稍后再试~~~"
                        else:
                            return get_image_url_data
                    else:
                        return get_image_url_data
                else:
                    logger.error("Error occurred: %s" % response.text)
                    return "哦豁，出现了未知错误，请联系管理员~~~"
            except Exception as e:
                logger.error("Error occurred: %s" % str(e))
                return "哦豁，出现了未知错误，请联系管理员~~~"
    # 提交变换任务的函数
    def get_simple(self, content):
        """
        提交变换任务

        参数:
            content (str): 变换内容

        返回:
            返回任务结果数据
        """
        data = {"content": content}
        api_url = f"{self.domain_name}/mj/submit/simple-change"

        headers = {
            "mj-api-secret": self.api_key
        }

        # 发送POST请求
        try:
            response = requests.post(url=api_url, headers=headers, json=data, timeout=120.05)
            if response.status_code == 200:
                get_imagine_data = response.json()
                logger.debug("get_imagine_data: %s" % get_imagine_data)
                return get_imagine_data
            else:
                logger.error("Error occurred: %s" % response.text)
                return "哦豁，出现了未知错误，请联系管理员~~~"
        except Exception as e:
            logger.error("Error occurred: %s" % str(e))
            return "哦豁，出现了未知错误，请联系管理员~~~"

    # 提交混合任务的函数
    def submit_blend(self, base64_data, dimensions="SQUARE"):
        """
        提交混合任务

        参数:
            base64_data (list): 包含2到5个元素的图像的base64编码数据
            dimensions (str): 图像比例（默认为SQUARE）

        返回:
            返回任务结果数据
        """
        assert isinstance(base64_data, list) and 2 <= len(base64_data) <= 5, "base64_data should be a list with 2 to 5 items."

        url = f"{self.domain_name}/mj/submit/blend"
        headers = {"Content-Type": "application/json", "mj-api-secret": self.api_key}
        data = {
            "base64Array": base64_data,
            "dimensions": dimensions,
            "notifyHook": "",
            "state": ""
        }

        # 发送POST请求
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                get_imagine_data = response.json()
                logger.debug("get_imagine_data: %s" % get_imagine_data)
                return get_imagine_data
            else:
                logger.error("Error occurred: %s" % response.text)
                return "哦豁，出现了未知错误，请联系管理员~~~"
        except Exception as e:
            logger.error("Error occurred: %s" % str(e))
            return "哦豁，出现了未知错误，请联系管理员~~~"
