import requests


class MyApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def client_set_callback_url(self, callback_url: str):
        """
        设置接收通知地址
        """
        return requests.post(f"{self.base_url}/global/callback-url", json={"callback_url": callback_url}).json()

    def user_get_profile(self, guid: str):
        """
        获取自己的信息
        """
        return requests.post(f"{self.base_url}/user/profile", json={"guid": guid}).json()

    def get_inner_contacts(self, guid: str, page_num: int = 1, page_size: int = 500):
        """
        获取同事列表
        """
        return requests.post(f"{self.base_url}/contacts/inner",
                             json={"guid": guid, "page_num": page_num, "page_size": page_size}).json()

    def get_external_contacts(self, guid: str, page_num: int = 1, page_size: int = 500):
        """
        获取客户列表
        """
        return requests.post(f"{self.base_url}/contacts/external",
                             json={"guid": guid, "page_num": page_num, "page_size": page_size}).json()

    def get_contact_detail(self, guid: str, user_id: str):
        """
        获取指定联系人详细信息
        """
        return requests.post(f"{self.base_url}/contacts/detail",
                             json={"guid": guid, "user_id": user_id}).json()

    def get_rooms(self, guid: str):
        """
        获取群列表
        """
        return requests.post(f"{self.base_url}/rooms/rooms", json={"guid": guid}).json()

    def get_room_members(self, guid: str, conversation_id: str, page_num: int = 1, page_size: int = 500):
        """
        获取群成员列表
        """
        return requests.post(f"{self.base_url}/rooms/members",
                             json={"guid": guid, "conversation_id": conversation_id, "page_num": page_num,
                                   "page_size": page_size}).json()

    def msg_send_text(self, guid: str, conversation_id: str, content: str):
        """
        发送文本消息
        """
        return requests.post(f"{self.base_url}/messages/text",
                             json={"guid": guid, "conversation_id": conversation_id, "content": content}).json()

    def send_room_at(self, guid: str, conversation_id: str, content: str, at_list: list):
        """
        发送群@消息
        """
        return requests.post(f"{self.base_url}/messages/room-at",
                             json={"guid": guid, "conversation_id": conversation_id, "content": content,
                                   "at_list": at_list}).json()

    def send_card(self, guid: str, conversation_id: str, user_id: str):
        """
        发送名片
        """
        return requests.post(f"{self.base_url}/messages/card",
                             json={"guid": guid, "conversation_id": conversation_id, "user_id": user_id}).json()

    def send_link_card(self, guid: str, conversation_id: str, title: str, desc: str, url: str, image_url: str):
        """
        发送链接卡片消息
        """
        return requests.post(f"{self.base_url}/messages/link",
                             json={"guid": guid, "conversation_id": conversation_id, "title": title, "desc": desc,
                                   "url": url, "image_url": image_url}).json()

    def send_image(self, guid: str, conversation_id: str, file_path: str):
        """
        发送图片
        """
        return requests.post(f"{self.base_url}/messages/image",
                             json={"guid": guid, "conversation_id": conversation_id, "file_path": file_path}).json()

    def send_file(self, guid: str, conversation_id: str, file_path: str):
        """
        发送文件
        """
        return requests.post(f"{self.base_url}/messages/file",
                             json={"guid": guid, "conversation_id": conversation_id, "file_path": file_path}).json()

    def send_video(self, guid: str, conversation_id: str, file_path: str):
        """
        发送视频
        """
        return requests.post(f"{self.base_url}/messages/video",
                             json={"guid": guid, "conversation_id": conversation_id, "file_path": file_path}).json()

    def send_gif(self, guid: str, conversation_id: str, file_path: str):
        """
        发送GIF
        """
        return requests.post(f"{self.base_url}/messages/gif",
                             json={"guid": guid, "conversation_id": conversation_id, "file_path": file_path}).json()

    def send_voice(self, guid: str, conversation_id, file_id, size, voice_time, aes_key, md5):
        """
        发送语音
        """
        return requests.post(f"{self.base_url}/messages/voice",
                             json={"guid": guid, "conversation_id": conversation_id, "file_id": file_id, "size": size,
                                   "voice_time": voice_time, "aes_key": aes_key, "md5": md5}).json()

    def cdn_upload(self, guid: str, file_path, file_type):
        """
        上传CDN文件
        """
        return requests.post(f"{self.base_url}/cdn/upload",
                             json={"guid": guid, "file_path": file_path, "file_type": file_type}).json()

    def c2c_cdn_download(self, guid: str, file_id, aes_key, file_size, file_type, save_path):
        """
        下载c2c类型的cdn文件
        """
        return requests.post(f"{self.base_url}/cdn/c2c-download",
                             json={"guid": guid, "file_id": file_id, "aes_key": aes_key, "file_size": file_size,
                                   "file_type": file_type, "save_path": save_path}).json()

    def wx_cdn_download(self, guid: str, url, auth_key, aes_key, size, save_path):
        """
        下载wx类型的cdn文件
        """
        return requests.post(f"{self.base_url}/cdn/wx-download",
                             json={"guid": guid, "url": url, "auth_key": auth_key, "aes_key": aes_key, "size": size,
                                   "save_path": save_path}).json()

    def accept_friend(self, guid: str, user_id, corp_id):
        """
        同意加好友请求
        """
        return requests.post(f"{self.base_url}/contacts/accept",
                             json={"guid": guid, "user_id": user_id, "corp_id": corp_id}).json()

    def send_miniapp(self, guid: str, conversation_id, aes_key, file_id, size, appicon, appid, appname, page_path, title,
                     username):
        """
        发送小程序
        """
        return requests.post(f"{self.base_url}/messages/miniapp",
                             json={"guid": guid, "aes_key": aes_key, "file_id": file_id, "size": size,
                                   "appicon": appicon, "appid": appid, "appname": appname,
                                   "conversation_id": conversation_id, "page_path": page_path, "title": title,
                                   "username": username}).json()

    def invite_to_room(self, guid: str, user_list: list, conversation_id: str):
        """
        添加或邀请好友进群
        """
        return requests.post(f"{self.base_url}/rooms/invite",
                             json={"guid": guid, "user_list": user_list, "conversation_id": conversation_id}).json()

    def create_empty_room(self, guid: str):
        """
        创建空外部群聊
        """
        return requests.post(f"{self.base_url}/rooms/empty-room", json={"guid": guid}).json()

    def exit_room(self, guid: str, room_conversation_id: str):
        """
        退出指定群聊
        """
        return requests.post(f"{self.base_url}/rooms/exit",
                             json={"guid": guid, "room_conversation_id": room_conversation_id}).json()
