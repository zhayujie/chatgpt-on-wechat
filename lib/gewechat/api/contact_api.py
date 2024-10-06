from ..util.http_util import post_json

class ContactApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def fetch_contacts_list(self, app_id):
        """获取通讯录列表"""
        param = {
            "appId": app_id
        }
        return post_json(self.base_url, "/contacts/fetchContactsList", self.token, param)

    def get_brief_info(self, app_id, wxids):
        """获取群/好友简要信息"""
        param = {
            "appId": app_id,
            "wxids": wxids
        }
        return post_json(self.base_url, "/contacts/getBriefInfo", self.token, param)

    def get_detail_info(self, app_id, wxids):
        """获取群/好友详细信息"""
        param = {
            "appId": app_id,
            "wxids": wxids
        }
        return post_json(self.base_url, "/contacts/getDetailInfo", self.token, param)

    def search(self, app_id, contacts_info):
        """搜索好友"""
        param = {
            "appId": app_id,
            "contactsInfo": contacts_info
        }
        return post_json(self.base_url, "/contacts/search", self.token, param)

    def add_contacts(self, app_id, scene, option, v3, v4, content):
        """添加联系人/同意添加好友"""
        param = {
            "appId": app_id,
            "scene": scene,
            "option": option,
            "v3": v3,
            "v4": v4,
            "content": content
        }
        return post_json(self.base_url, "/contacts/addContacts", self.token, param)

    def delete_friend(self, app_id, wxid):
        """删除好友"""
        param = {
            "appId": app_id,
            "wxid": wxid
        }
        return post_json(self.base_url, "/contacts/deleteFriend", self.token, param)

    def set_friend_permissions(self, app_id, wxid, only_chat):
        """设置好友仅聊天"""
        param = {
            "appId": app_id,
            "wxid": wxid,
            "onlyChat": only_chat
        }
        return post_json(self.base_url, "/contacts/setFriendPermissions", self.token, param)

    def set_friend_remark(self, app_id, wxid, remark):
        """设置好友备注"""
        param = {
            "appId": app_id,
            "wxid": wxid,
            "onlyChat": remark
        }
        return post_json(self.base_url, "/contacts/setFriendRemark", self.token, param)

    def get_phone_address_list(self, app_id, phones):
        """获取手机通讯录"""
        param = {
            "appId": app_id,
            "wxid": phones
        }
        return post_json(self.base_url, "/contacts/getPhoneAddressList", self.token, param)

    def upload_phone_address_list(self, app_id, phones, op_type):
        """上传手机通讯录"""
        param = {
            "appId": app_id,
            "wxid": phones,
            "opType": op_type
        }
        return post_json(self.base_url, "/contacts/uploadPhoneAddressList", self.token, param)