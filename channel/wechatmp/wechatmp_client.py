import time
import json
import requests
import threading
from channel.wechatmp.common import *
from common.log import logger
from config import conf


class WechatMPClient:
    def __init__(self):
        self.app_id = conf().get("wechatmp_app_id")
        self.app_secret = conf().get("wechatmp_app_secret")
        self.access_token = None
        self.access_token_expires_time = 0
        self.access_token_lock = threading.Lock()
        self.get_access_token()


    def wechatmp_request(self, method, url, **kwargs):
        r = requests.request(method=method, url=url, **kwargs)
        r.raise_for_status()
        r.encoding = "utf-8"
        ret = r.json()
        if "errcode" in ret and ret["errcode"] != 0:
            if ret["errcode"] == 45009:
                self.clear_quota_v2()
            raise WeChatAPIException("{}".format(ret))
        return ret

    def get_access_token(self):
        # return the access_token
        if self.access_token:
            if self.access_token_expires_time - time.time() > 60:
                return self.access_token

        # Get new access_token
        # Do not request access_token in parallel! Only the last obtained is valid.
        if self.access_token_lock.acquire(blocking=False):
            # Wait for other threads that have previously obtained access_token to complete the request
            # This happens every 2 hours, so it doesn't affect the experience very much
            time.sleep(1)
            self.access_token = None
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            }
            ret = self.wechatmp_request(method="get", url=url, params=params)
            self.access_token = ret["access_token"]
            self.access_token_expires_time = int(time.time()) + ret["expires_in"]
            logger.info("[wechatmp] access_token: {}".format(self.access_token))
            self.access_token_lock.release()
        else:
            # Wait for token update
            while self.access_token_lock.locked():
                time.sleep(0.1)
        return self.access_token


    def send_text(self, receiver, reply_text):
        url = "https://api.weixin.qq.com/cgi-bin/message/custom/send"
        params = {"access_token": self.get_access_token()}
        json_data = {
            "touser": receiver,
            "msgtype": "text",
            "text": {"content": reply_text},
        }
        self.wechatmp_request(
            method="post",
            url=url,
            params=params,
            data=json.dumps(json_data, ensure_ascii=False).encode("utf8"),
        )


    def send_voice(self, receiver, media_id):
        url="https://api.weixin.qq.com/cgi-bin/message/custom/send"
        params = {"access_token": self.get_access_token()}
        json_data = {
            "touser": receiver,
            "msgtype": "voice",
            "voice": {
                "media_id": media_id
            }
        }
        self.wechatmp_request(
            method="post",
            url=url,
            params=params,
            data=json.dumps(json_data, ensure_ascii=False).encode("utf8"),
        )

    def send_image(self, receiver, media_id):
        url="https://api.weixin.qq.com/cgi-bin/message/custom/send"
        params = {"access_token": self.get_access_token()}
        json_data = {
            "touser": receiver,
            "msgtype": "image",
            "image": {
                "media_id": media_id
            }
        }
        self.wechatmp_request(
            method="post",
            url=url,
            params=params,
            data=json.dumps(json_data, ensure_ascii=False).encode("utf8"),
        )


    def upload_media(self, media_type, media_file):
        url="https://api.weixin.qq.com/cgi-bin/media/upload"
        params={
            "access_token": self.get_access_token(),
            "type": media_type
        }
        files={"media": media_file}
        ret = self.wechatmp_request(
            method="post",
            url=url,
            params=params,
            files=files
        )
        logger.debug("[wechatmp] media {} uploaded".format(media_file))
        return ret["media_id"]


    def upload_permanent_media(self, media_type, media_file):
        url="https://api.weixin.qq.com/cgi-bin/material/add_material"
        params={
            "access_token": self.get_access_token(),
            "type": media_type
        }
        files={"media": media_file}
        ret = self.wechatmp_request(
            method="post",
            url=url,
            params=params,
            files=files
        )
        logger.debug("[wechatmp] permanent media {} uploaded".format(media_file))
        return ret["media_id"]


    def delete_permanent_media(self, media_id):
        url="https://api.weixin.qq.com/cgi-bin/material/del_material"
        params={
            "access_token": self.get_access_token()
        }
        self.wechatmp_request(
            method="post",
            url=url,
            params=params,
            data=json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf8")
        )
        logger.debug("[wechatmp] permanent media {} deleted".format(media_id))

    def clear_quota(self):
        url="https://api.weixin.qq.com/cgi-bin/clear_quota"
        params = {
            "access_token": self.get_access_token()
        }
        self.wechatmp_request(
            method="post",
            url=url,
            params=params,
            data={"appid": self.app_id}
        )
        logger.debug("[wechatmp] API quata has been cleard")

    def clear_quota_v2(self):
        url="https://api.weixin.qq.com/cgi-bin/clear_quota/v2"
        self.wechatmp_request(
            method="post",
            url=url,
            data={"appid": self.app_id, "appsecret": self.app_secret}
        )
        logger.debug("[wechatmp] API quata has been cleard")
