from ..util.http_util import post_json

class FavorApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def sync(self, app_id, sync_key):
        """同步收藏夹"""
        param = {
            "appId": app_id,
            "syncKey": sync_key
        }
        return post_json(self.base_url, "/favor/sync", self.token, param)

    def get_content(self, app_id, fav_id):
        """获取收藏夹内容"""
        param = {
            "appId": app_id,
            "favId": fav_id
        }
        return post_json(self.base_url, "/favor/getContent", self.token, param)

    def delete(self, app_id, fav_id):
        """删除收藏夹"""
        param = {
            "appId": app_id,
            "favId": fav_id
        }
        return post_json(self.base_url, "/favor/delete", self.token, param)