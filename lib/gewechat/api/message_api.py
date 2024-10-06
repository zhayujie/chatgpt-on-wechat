from ..util.http_util import post_json

class MessageApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def post_text(self, app_id, to_wxid, content, ats):
        """发送文字消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "content": content,
            "ats": ats
        }
        return post_json(self.base_url, "/message/postText", self.token, param)

    def post_file(self, app_id, to_wxid, file_url, file_name):
        """发送文件消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "fileUrl": file_url,
            "fileName": file_name
        }
        return post_json(self.base_url, "/message/postFile", self.token, param)

    def post_image(self, app_id, to_wxid, img_url):
        """发送图片消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "imgUrl": img_url
        }
        return post_json(self.base_url, "/message/postImage", self.token, param)

    def post_voice(self, app_id, to_wxid, voice_url, voice_duration):
        """发送语音消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "voiceUrl": voice_url,
            "voiceDuration": voice_duration
        }
        return post_json(self.base_url, "/message/postVoice", self.token, param)

    def post_video(self, app_id, to_wxid, video_url, thumb_url, video_duration):
        """发送视频消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "videoUrl": video_url,
            "thumbUrl": thumb_url,
            "videoDuration": video_duration
        }
        return post_json(self.base_url, "/message/postVideo", self.token, param)

    def post_link(self, app_id, to_wxid, title, desc, link_url, thumb_url):
        """发送链接消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "title": title,
            "desc": desc,
            "linkUrl": link_url,
            "thumbUrl": thumb_url
        }
        return post_json(self.base_url, "/message/postLink", self.token, param)

    def post_name_card(self, app_id, to_wxid, nick_name, name_card_wxid):
        """发送名片消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "nickName": nick_name,
            "nameCardWxid": name_card_wxid
        }
        return post_json(self.base_url, "/message/postNameCard", self.token, param)

    def post_emoji(self, app_id, to_wxid, emoji_md5, emoji_size):
        """发送emoji消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "emojiMd5": emoji_md5,
            "emojiSize": emoji_size
        }
        return post_json(self.base_url, "/message/postEmoji", self.token, param)

    def post_app_msg(self, app_id, to_wxid, appmsg):
        """发送appmsg消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "appmsg": appmsg
        }
        return post_json(self.base_url, "/message/postAppMsg", self.token, param)

    def post_mini_app(self, app_id, to_wxid, mini_app_id, display_name, page_path, cover_img_url, title, user_name):
        """发送小程序消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "miniAppId": mini_app_id,
            "displayName": display_name,
            "pagePath": page_path,
            "coverImgUrl": cover_img_url,
            "title": title,
            "userName": user_name
        }
        return post_json(self.base_url, "/message/postMiniApp", self.token, param)

    def forward_file(self, app_id, to_wxid, xml):
        """转发文件"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardFile", self.token, param)

    def forward_image(self, app_id, to_wxid, xml):
        """转发图片"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardImage", self.token, param)

    def forward_video(self, app_id, to_wxid, xml):
        """转发视频"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardVideo", self.token, param)

    def forward_url(self, app_id, to_wxid, xml):
        """转发链接"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml
        }
        return post_json(self.base_url, "/message/forwardUrl", self.token, param)

    def forward_mini_app(self, app_id, to_wxid, xml, cover_img_url):
        """转发小程序"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "xml": xml,
            "coverImgUrl": cover_img_url
        }
        return post_json(self.base_url, "/message/forwardMiniApp", self.token, param)

    def revoke_msg(self, app_id, to_wxid, msg_id, new_msg_id, create_time):
        """撤回消息"""
        param = {
            "appId": app_id,
            "toWxid": to_wxid,
            "msgId": msg_id,
            "newMsgId": new_msg_id,
            "createTime": create_time
        }
        return post_json(self.base_url, "/message/revokeMsg", self.token, param)