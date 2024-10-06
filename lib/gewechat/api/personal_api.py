from ..util.http_util import post_json

class PersonalApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def get_profile(self, app_id):
        """获取个人资料"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/personal/getProfile", self.token, param)

    def get_qr_code(self, app_id):
        """获取自己的二维码"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/personal/getQrCode", self.token, param)

    def get_safety_info(self, app_id):
        """获取设备记录"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/personal/getSafetyInfo", self.token, param)

    def privacy_settings(self, app_id, option, open):
        """隐私设置"""
        param = {
            "appId": app_id,
            "option": option,
            "open": open
        }
        return post_json(self.base_url, "/personal/privacySettings", self.token, param)

    def update_profile(self, app_id, city, country, nick_name, province, sex, signature):
        """修改个人信息"""
        param = {
            "appId": app_id,
            "city": city,
            "country": country,
            "nickName": nick_name,
            "province": province,
            "sex": sex,
            "signature": signature
        }
        return post_json(self.base_url, "/personal/updateProfile", self.token, param)

    def update_head_img(self, app_id, head_img_url):
        """修改头像"""
        param = {
            "appId": app_id,
            "headImgUrl": head_img_url
        }
        return post_json(self.base_url, "/personal/updateHeadImg", self.token, param)