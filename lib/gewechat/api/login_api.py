from ..util.http_util import post_json

class LoginApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def get_token(self):
        """获取tokenId 将tokenId 配置到OkhttpUtil 类中的token 属性"""
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