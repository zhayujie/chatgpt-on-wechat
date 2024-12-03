from ..util.terminal_printer import make_and_print_qr, print_green, print_yellow, print_red
from ..util.http_util import post_json
import time


class LoginApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def get_token(self):
        """获取tokenId"""
        return post_json(self.base_url, "/tools/getTokenId", self.token, {})

    def set_callback(self, token, callback_url):
        """设置微信消息的回调地址"""
        param = {
            "token": token,
            "callbackUrl": callback_url
        }
        return post_json(self.base_url, "/tools/setCallback", self.token, param)

    def get_qr(self, app_id):
        """获取登录二维码"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/login/getLoginQrCode", self.token, param)

    def check_qr(self, app_id, uuid, captch_code):
        """确认登陆"""
        param = {
            "appId": app_id,
            "uuid": uuid,
            "captchCode": captch_code
        }
        return post_json(self.base_url, "/login/checkLogin", self.token, param)

    def log_out(self, app_id):
        """退出微信"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/login/logout", self.token, param)

    def dialog_login(self, app_id):
        """弹框登录"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/login/dialogLogin", self.token, param)

    def check_online(self, app_id):
        """检查是否在线"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/login/checkOnline", self.token, param)

    def logout(self, app_id):
        """退出"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/login/logout", self.token, param)

    def _get_and_validate_qr(self, app_id):
        """获取并验证二维码数据

        Args:
            app_id: 应用ID

        Returns:
            tuple: (app_id, uuid) 或在失败时返回 (None, None)
        """

        qr_response = self.get_qr(app_id)
        if qr_response.get('ret') != 200:
            print_yellow(f"获取二维码失败:", qr_response)
            return None, None

        qr_data = qr_response.get('data', {})
        app_id = qr_data.get('appId')
        uuid = qr_data.get('uuid')
        if not app_id or not uuid:
            print_yellow(f"app_id: {app_id}, uuid: {uuid}, 获取app_id或uuid失败")
            return None, None

        return app_id, uuid

    def login(self, app_id):
        """执行完整的登录流程
        
        Args:
            app_id: 可选的应用ID，为空时会自动创建新的app_id
            
        Returns:
            tuple: (app_id: str, error_msg: str) 
                   成功时 error_msg 为空字符串
                   失败时 app_id 可能为空字符串，error_msg 包含错误信息
        """
        # 1. 检查是否已经登录
        input_app_id = app_id
        if input_app_id:
            check_online_response = self.check_online(input_app_id)
            if check_online_response.get('ret') == 200 and check_online_response.get('data'):
                print_green(f"AppID: {input_app_id} 已在线，无需登录")
                return input_app_id, ""
            else:
                print_yellow(f"AppID: {input_app_id} 未在线，执行登录流程")

        # 2. 获取初始二维码
        app_id, uuid = self._get_and_validate_qr(app_id)
        if not app_id or not uuid:
            return "", "获取二维码失败"

        if not input_app_id:
            print_green(f"AppID: {app_id}, 请保存此app_id，下次登录时继续使用!")
            print_yellow("\n新设备登录平台，次日凌晨会掉线一次，重新登录时需使用原来的app_id取码，否则新app_id仍然会掉线，登录成功后则可以长期在线")

        make_and_print_qr(f"http://weixin.qq.com/x/{uuid}")

        # 3. 轮询检查登录状态
        retry_count = 0
        max_retries = 100  # 最大重试100次
        
        while retry_count < max_retries:
            login_status = self.check_qr(app_id, uuid, "")
            if login_status.get('ret') != 200:
                print_red(f"检查登录状态失败: {login_status}")
                return app_id, f"检查登录状态失败: {login_status}"

            login_data = login_status.get('data', {})
            status = login_data.get('status')
            expired_time = login_data.get('expiredTime', 0)
            
            # 检查二维码是否过期，提前5秒重新获取
            if expired_time <= 5:
                print_yellow("二维码即将过期，正在重新获取...")
                _, uuid = self._get_and_validate_qr(app_id)
                if not uuid:
                    return app_id, "重新获取二维码失败"

                make_and_print_qr(f"http://weixin.qq.com/x/{uuid}")
                continue

            if status == 2:  # 登录成功
                nick_name = login_data.get('nickName', '未知用户')
                print_green(f"\n登录成功！用户昵称: {nick_name}")
                return app_id, ""
            else:
                retry_count += 1
                if retry_count >= max_retries:
                    print_yellow("登录超时，请重新尝试")
                    return False
                time.sleep(5)
