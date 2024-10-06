from ..util.http_util import post_json

class LabelApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def add(self, app_id, label_name):
        """添加标签"""
        param = {
            "appId": app_id,
            "labelName": label_name
        }
        return post_json(self.base_url, "/label/add", self.token, param)

    def delete(self, app_id, label_ids):
        """删除标签"""
        param = {
            "appId": app_id,
            "labelIds": label_ids
        }
        return post_json(self.base_url, "/label/delete", self.token, param)

    def list(self, app_id):
        """获取标签列表"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/label/list", self.token, param)

    def modify_member_list(self, app_id, label_ids, wx_ids):
        """修改标签成员列表"""
        param = {
            "appId": app_id,
            "labelIds": label_ids,
            "wxIds": wx_ids
        }
        return post_json(self.base_url, "/label/modifyMemberList", self.token, param)