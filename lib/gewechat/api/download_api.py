from ..util.http_util import post_json

class DownloadApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def download_image(self, app_id, xml, type):
        """下载图片"""
        param = {
            "appId": app_id,
            "xml": xml,
            "type": type
        }
        return post_json(self.base_url, "/message/downloadImage", self.token, param)

    def download_voice(self, app_id, xml, msg_id):
        """下载语音"""
        param = {
            "appId": app_id,
            "xml": xml,
            "msgId": msg_id
        }
        return post_json(self.base_url, "/message/downloadVoice", self.token, param)

    def download_video(self, app_id, xml):
        """下载视频"""
        param = {
            "appId": app_id,
            "xml": xml
        }
        return post_json(self.base_url, "/message/downloadVideo", self.token, param)

    def download_emoji_md5(self, app_id, emoji_md5):
        """下载emoji"""
        param = {
            "appId": app_id,
            "emojiMd5": emoji_md5
        }
        return post_json(self.base_url, "/message/downloadEmojiMd5", self.token, param)

    def download_cdn(self, app_id, aes_key, file_id, type, total_size, suffix):
        """cdn下载"""
        param = {
            "appId": app_id,
            "aesKey": aes_key,
            "fileId": file_id,
            "totalSize": total_size,
            "type": type,
            "suffix": suffix
        }
        return post_json(self.base_url, "/message/downloadCdn", self.token, param)