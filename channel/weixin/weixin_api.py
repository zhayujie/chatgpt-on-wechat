"""
Weixin HTTP JSON API client.

Implements the ilink bot protocol:
  - getUpdates (long-poll)
  - sendMessage
  - getUploadUrl
  - getConfig
  - sendTyping
  - QR login (get_bot_qrcode / get_qrcode_status)

CDN media upload with AES-128-ECB encryption.
"""

import base64
import hashlib
import os
import random
import struct
import time
import uuid

import requests

from common.log import logger

DEFAULT_BASE_URL = "https://ilinkai.weixin.qq.com"
CDN_BASE_URL = "https://novac2c.cdn.weixin.qq.com/c2c"
DEFAULT_LONG_POLL_TIMEOUT = 35
DEFAULT_API_TIMEOUT = 15
QR_POLL_TIMEOUT = 35
BOT_TYPE = "3"


def _random_wechat_uin() -> str:
    val = random.randint(0, 0xFFFFFFFF)
    return base64.b64encode(str(val).encode("utf-8")).decode("utf-8")


def _build_headers(token: str = "") -> dict:
    headers = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "X-WECHAT-UIN": _random_wechat_uin(),
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"


class WeixinApi:
    """Stateless HTTP client for the Weixin ilink bot API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: str = "",
                 cdn_base_url: str = CDN_BASE_URL):
        self.base_url = base_url
        self.token = token
        self.cdn_base_url = cdn_base_url

    def _post(self, endpoint: str, body: dict, timeout: int = DEFAULT_API_TIMEOUT) -> dict:
        url = _ensure_trailing_slash(self.base_url) + endpoint
        headers = _build_headers(self.token)
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.debug(f"[Weixin] API timeout: {endpoint}")
            return {"ret": 0, "msgs": []}
        except Exception as e:
            logger.error(f"[Weixin] API error {endpoint}: {e}")
            raise

    # ── getUpdates (long-poll) ─────────────────────────────────────────

    def get_updates(self, get_updates_buf: str = "", timeout: int = DEFAULT_LONG_POLL_TIMEOUT) -> dict:
        return self._post("ilink/bot/getupdates", {
            "get_updates_buf": get_updates_buf,
        }, timeout=timeout + 5)

    # ── sendMessage ────────────────────────────────────────────────────

    def send_text(self, to: str, text: str, context_token: str) -> dict:
        return self._post("ilink/bot/sendmessage", {
            "msg": {
                "from_user_id": "",
                "to_user_id": to,
                "client_id": uuid.uuid4().hex[:16],
                "message_type": 2,  # BOT
                "message_state": 2,  # FINISH
                "item_list": [{"type": 1, "text_item": {"text": text}}],
                "context_token": context_token,
            }
        })

    def send_image_item(self, to: str, context_token: str,
                        encrypt_query_param: str, aes_key_b64: str,
                        ciphertext_size: int, text: str = "") -> dict:
        items = []
        if text:
            items.append({"type": 1, "text_item": {"text": text}})
        items.append({
            "type": 2,
            "image_item": {
                "media": {
                    "encrypt_query_param": encrypt_query_param,
                    "aes_key": aes_key_b64,
                    "encrypt_type": 1,
                },
                "mid_size": ciphertext_size,
            }
        })
        return self._send_items(to, context_token, items)

    def send_file_item(self, to: str, context_token: str,
                       encrypt_query_param: str, aes_key_b64: str,
                       file_name: str, file_size: int, text: str = "") -> dict:
        items = []
        if text:
            items.append({"type": 1, "text_item": {"text": text}})
        items.append({
            "type": 4,
            "file_item": {
                "media": {
                    "encrypt_query_param": encrypt_query_param,
                    "aes_key": aes_key_b64,
                    "encrypt_type": 1,
                },
                "file_name": file_name,
                "len": str(file_size),
            }
        })
        return self._send_items(to, context_token, items)

    def send_video_item(self, to: str, context_token: str,
                        encrypt_query_param: str, aes_key_b64: str,
                        ciphertext_size: int, text: str = "") -> dict:
        items = []
        if text:
            items.append({"type": 1, "text_item": {"text": text}})
        items.append({
            "type": 5,
            "video_item": {
                "media": {
                    "encrypt_query_param": encrypt_query_param,
                    "aes_key": aes_key_b64,
                    "encrypt_type": 1,
                },
                "video_size": ciphertext_size,
            }
        })
        return self._send_items(to, context_token, items)

    def _send_items(self, to: str, context_token: str, items: list) -> dict:
        return self._post("ilink/bot/sendmessage", {
            "msg": {
                "from_user_id": "",
                "to_user_id": to,
                "client_id": uuid.uuid4().hex[:16],
                "message_type": 2,
                "message_state": 2,
                "item_list": items,
                "context_token": context_token,
            }
        })

    # ── getUploadUrl ───────────────────────────────────────────────────

    def get_upload_url(self, filekey: str, media_type: int, to_user_id: str,
                       rawsize: int, rawfilemd5: str, filesize: int,
                       aeskey: str,
                       thumb_rawsize: int = 0, thumb_rawfilemd5: str = "",
                       thumb_filesize: int = 0) -> dict:
        body = {
            "filekey": filekey,
            "media_type": media_type,
            "to_user_id": to_user_id,
            "rawsize": rawsize,
            "rawfilemd5": rawfilemd5,
            "filesize": filesize,
            "aeskey": aeskey,
        }
        if thumb_rawsize > 0:
            body["thumb_rawsize"] = thumb_rawsize
            body["thumb_rawfilemd5"] = thumb_rawfilemd5
            body["thumb_filesize"] = thumb_filesize
        else:
            body["no_need_thumb"] = True
        return self._post("ilink/bot/getuploadurl", body)

    # ── getConfig / sendTyping ─────────────────────────────────────────

    def get_config(self, user_id: str, context_token: str = "") -> dict:
        return self._post("ilink/bot/getconfig", {
            "ilink_user_id": user_id,
            "context_token": context_token,
        }, timeout=10)

    def send_typing(self, user_id: str, typing_ticket: str, status: int = 1) -> dict:
        return self._post("ilink/bot/sendtyping", {
            "ilink_user_id": user_id,
            "typing_ticket": typing_ticket,
            "status": status,
        }, timeout=10)

    # ── QR Login ───────────────────────────────────────────────────────

    def fetch_qr_code(self) -> dict:
        url = _ensure_trailing_slash(self.base_url) + f"ilink/bot/get_bot_qrcode?bot_type={BOT_TYPE}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def poll_qr_status(self, qrcode: str, timeout: int = QR_POLL_TIMEOUT) -> dict:
        url = (_ensure_trailing_slash(self.base_url) +
               f"ilink/bot/get_qrcode_status?qrcode={requests.utils.quote(qrcode)}")
        headers = {"iLink-App-ClientVersion": "1"}
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            return {"status": "wait"}


# ── AES-128-ECB helpers ─────────────────────────────────────────────

def _aes_ecb_encrypt(data: bytes, key: bytes) -> bytes:
    from Crypto.Cipher import AES
    pad_len = 16 - (len(data) % 16)
    padded = data + bytes([pad_len] * pad_len)
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(padded)


def _aes_ecb_decrypt(data: bytes, key: bytes) -> bytes:
    from Crypto.Cipher import AES
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(data)
    pad_len = decrypted[-1]
    if pad_len > 16:
        return decrypted
    return decrypted[:-pad_len]


def _file_md5(file_path: str) -> str:
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def upload_media_to_cdn(api: WeixinApi, file_path: str, to_user_id: str,
                        media_type: int) -> dict:
    """
    Upload a local file to the Weixin CDN.

    Args:
        api: WeixinApi instance
        file_path: local file path
        to_user_id: target user id
        media_type: 1=IMAGE, 2=VIDEO, 3=FILE

    Returns:
        dict with keys: encrypt_query_param, aes_key_b64, ciphertext_size, raw_size
    """
    aes_key = os.urandom(16)
    aes_key_hex = aes_key.hex()

    with open(file_path, "rb") as f:
        raw_data = f.read()

    raw_size = len(raw_data)
    raw_md5 = _md5_bytes(raw_data)
    encrypted = _aes_ecb_encrypt(raw_data, aes_key)
    cipher_size = len(encrypted)
    filekey = uuid.uuid4().hex

    thumb_rawsize = 0
    thumb_rawfilemd5 = ""
    thumb_filesize = 0

    if media_type == 1:  # IMAGE - generate a tiny thumbnail
        try:
            from PIL import Image
            import io
            img = Image.open(file_path)
            img.thumbnail((100, 100))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=60)
            thumb_raw = buf.getvalue()
            thumb_rawsize = len(thumb_raw)
            thumb_rawfilemd5 = _md5_bytes(thumb_raw)
            thumb_encrypted = _aes_ecb_encrypt(thumb_raw, aes_key)
            thumb_filesize = len(thumb_encrypted)
        except Exception as e:
            logger.warning(f"[Weixin] Thumbnail generation failed, skipping: {e}")

    resp = api.get_upload_url(
        filekey=filekey,
        media_type=media_type,
        to_user_id=to_user_id,
        rawsize=raw_size,
        rawfilemd5=raw_md5,
        filesize=cipher_size,
        aeskey=aes_key_hex,
        thumb_rawsize=thumb_rawsize,
        thumb_rawfilemd5=thumb_rawfilemd5,
        thumb_filesize=thumb_filesize,
    )

    upload_param = resp.get("upload_param", "")
    if not upload_param:
        raise RuntimeError(f"[Weixin] getUploadUrl returned no upload_param: {resp}")

    cdn_url = api.cdn_base_url + "?" + upload_param
    put_resp = requests.put(cdn_url, data=encrypted, headers={
        "Content-Type": "application/octet-stream",
        "Content-Length": str(cipher_size),
    }, timeout=60)
    put_resp.raise_for_status()

    # Upload thumbnail if we have one
    thumb_upload_param = resp.get("thumb_upload_param", "")
    if thumb_upload_param and thumb_filesize > 0:
        thumb_cdn_url = api.cdn_base_url + "?" + thumb_upload_param
        try:
            requests.put(thumb_cdn_url, data=thumb_encrypted, headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(thumb_filesize),
            }, timeout=30)
        except Exception as e:
            logger.warning(f"[Weixin] Thumbnail upload failed (non-fatal): {e}")

    return {
        "encrypt_query_param": upload_param,
        "aes_key_b64": base64.b64encode(aes_key).decode("utf-8"),
        "ciphertext_size": cipher_size,
        "raw_size": raw_size,
    }


def download_media_from_cdn(cdn_base_url: str, encrypt_query_param: str,
                            aes_key: str, save_path: str) -> str:
    """
    Download and decrypt a media file from Weixin CDN.

    Args:
        cdn_base_url: CDN base URL
        encrypt_query_param: encrypted query parameter from message
        aes_key: hex or base64 encoded AES key
        save_path: path to save decrypted file

    Returns:
        save_path on success
    """
    url = cdn_base_url + "?" + encrypt_query_param
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    # Determine key format (hex string or base64)
    try:
        key_bytes = bytes.fromhex(aes_key)
        if len(key_bytes) != 16:
            raise ValueError()
    except (ValueError, TypeError):
        key_bytes = base64.b64decode(aes_key)
        if len(key_bytes) != 16:
            raise ValueError(f"Invalid AES key length: {len(key_bytes)}")

    decrypted = _aes_ecb_decrypt(resp.content, key_bytes)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(decrypted)
    return save_path
