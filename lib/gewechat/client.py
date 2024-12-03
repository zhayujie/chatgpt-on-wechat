from .api.contact_api import ContactApi
from .api.download_api import DownloadApi
from .api.download_api import DownloadApi
from .api.favor_api import FavorApi
from .api.group_api import GroupApi
from .api.label_api import LabelApi
from .api.login_api import LoginApi
from .api.message_api import MessageApi
from .api.personal_api import PersonalApi

class GewechatClient:
    """
    GewechatClient 是一个用于与GeWeChat服务进行交互的客户端类。
    它提供了多种方法来执行各种微信相关的操作，如管理联系人、群组、消息等。

    使用示例:
    ```
    # 初始化客户端
    client = GewechatClient("http://服务ip:2531/v2/api", "your_token_here")
    app_id = "your_app_id"
    # 获取联系人列表
    contacts = client.fetch_contacts_list(app_id)

    # 发送文本消息
    client.post_text(app_id, "wxid", "Hello, World!")

    # 获取个人资料
    profile = client.get_profile(app_id)
    ```

    注意: 在使用任何方法之前，请确保你已经正确初始化了客户端，并且有有效的 base_url 和 token。
    """
    def __init__(self, base_url, token):
        self._contact_api = ContactApi(base_url, token)
        self._download_api = DownloadApi(base_url, token)
        self._favor_api = FavorApi(base_url, token)
        self._group_api = GroupApi(base_url, token)
        self._label_api = LabelApi(base_url, token)
        self._login_api = LoginApi(base_url, token)
        self._message_api = MessageApi(base_url, token)
        self._personal_api = PersonalApi(base_url, token)

    def fetch_contacts_list(self, app_id):
        """获取通讯录列表"""
        return self._contact_api.fetch_contacts_list(app_id)

    def get_brief_info(self, app_id, wxids):
        """获取群/好友简要信息"""
        return self._contact_api.get_brief_info(app_id, wxids)

    def get_detail_info(self, app_id, wxids):
        """获取群/好友详细信息"""
        return self._contact_api.get_detail_info(app_id, wxids)

    def search_contacts(self, app_id, contacts_info):
        """搜索好友"""
        return self._contact_api.search(app_id, contacts_info)

    def add_contacts(self, app_id, scene, option, v3, v4, content):
        """添加联系人/同意添加好友"""
        return self._contact_api.add_contacts(app_id, scene, option, v3, v4, content)

    def delete_friend(self, app_id, wxid):
        """删除好友"""
        return self._contact_api.delete_friend(app_id, wxid)

    def set_friend_permissions(self, app_id, wxid, only_chat):
        """设置好友仅聊天"""
        return self._contact_api.set_friend_permissions(app_id, wxid, only_chat)

    def set_friend_remark(self, app_id, wxid, remark):
        """设置好友备注"""
        return self._contact_api.set_friend_remark(app_id, wxid, remark)

    def get_phone_address_list(self, app_id, phones):
        """获取手机通讯录"""
        return self._contact_api.get_phone_address_list(app_id, phones)

    def upload_phone_address_list(self, app_id, phones, op_type):
        """上传手机通讯录"""
        return self._contact_api.upload_phone_address_list(app_id, phones, op_type)

    def sync_favor(self, app_id, sync_key):
        """同步收藏夹"""
        return self._favor_api.sync(app_id, sync_key)
    
    def get_favor_content(self, app_id, fav_id):
        """获取收藏夹"""
        return self._favor_api.get_content(app_id, fav_id)

    def delete_favor(self, app_id, fav_id):
        """删除收藏夹"""
        return self._favor_api.delete(app_id, fav_id)

    def download_image(self, app_id, xml, type):
        """下载图片"""
        return self._download_api.download_image(app_id, xml, type)

    def download_voice(self, app_id, xml, msg_id):
        """下载语音"""
        return self._download_api.download_voice(app_id, xml, msg_id)

    def download_video(self, app_id, xml):
        """下载视频"""
        return self._download_api.download_video(app_id, xml)

    def download_emoji_md5(self, app_id, emoji_md5):
        """下载emoji"""
        return self._download_api.download_emoji_md5(app_id, emoji_md5)

    def download_cdn(self, app_id, aes_key, file_id, type, total_size, suffix):
        """cdn下载"""
        return self._download_api.download_cdn(app_id, aes_key, file_id, type, total_size, suffix)

    # Group API methods
    def create_chatroom(self, app_id, wxids):
        """创建微信群"""
        return self._group_api.create_chatroom(app_id, wxids)

    def modify_chatroom_name(self, app_id, chatroom_name, chatroom_id):
        """修改群名称"""
        return self._group_api.modify_chatroom_name(app_id, chatroom_name, chatroom_id)

    def modify_chatroom_remark(self, app_id, chatroom_remark, chatroom_id):
        """修改群备注"""
        return self._group_api.modify_chatroom_remark(app_id, chatroom_remark, chatroom_id)

    def modify_chatroom_nickname_for_self(self, app_id, nick_name, chatroom_id):
        """修改我在群内的昵称"""
        return self._group_api.modify_chatroom_nickname_for_self(app_id, nick_name, chatroom_id)

    def invite_member(self, app_id, wxids, chatroom_id, reason):
        """邀请/添加 进群"""
        return self._group_api.invite_member(app_id, wxids, chatroom_id, reason)

    def remove_member(self, app_id, wxids, chatroom_id):
        """删除群成员"""
        return self._group_api.remove_member(app_id, wxids, chatroom_id)

    def quit_chatroom(self, app_id, chatroom_id):
        """退出群聊"""
        return self._group_api.quit_chatroom(app_id, chatroom_id)

    def disband_chatroom(self, app_id, chatroom_id):
        """解散群聊"""
        return self._group_api.disband_chatroom(app_id, chatroom_id)

    def get_chatroom_info(self, app_id, chatroom_id):
        """获取群信息"""
        return self._group_api.get_chatroom_info(app_id, chatroom_id)

    def get_chatroom_member_list(self, app_id, chatroom_id):
        """获取群成员列表"""
        return self._group_api.get_chatroom_member_list(app_id, chatroom_id)

    def get_chatroom_member_detail(self, app_id, chatroom_id, member_wxids):
        """获取群成员详情"""
        return self._group_api.get_chatroom_member_detail(app_id, chatroom_id, member_wxids)

    def get_chatroom_announcement(self, app_id, chatroom_id):
        """获取群公告"""
        return self._group_api.get_chatroom_announcement(app_id, chatroom_id)

    def set_chatroom_announcement(self, app_id, chatroom_id, content):
        """设置群公告"""
        return self._group_api.set_chatroom_announcement(app_id, chatroom_id, content)

    def agree_join_room(self, app_id, url):
        """同意进群"""
        return self._group_api.agree_join_room(app_id, url)

    def add_group_member_as_friend(self, app_id, member_wxid, chatroom_id, content):
        """添加群成员为好友"""
        return self._group_api.add_group_member_as_friend(app_id, member_wxid, chatroom_id, content)

    def get_chatroom_qr_code(self, app_id, chatroom_id):
        """获取群二维码"""
        return self._group_api.get_chatroom_qr_code(app_id, chatroom_id)

    def save_contract_list(self, app_id, oper_type, chatroom_id):
        """群保存到通讯录或从通讯录移除"""
        return self._group_api.save_contract_list(app_id, oper_type, chatroom_id)

    def admin_operate(self, app_id, chatroom_id, wxids, oper_type):
        """管理员操作"""
        return self._group_api.admin_operate(app_id, chatroom_id, wxids, oper_type)

    def pin_chat(self, app_id, top, chatroom_id):
        """聊天置顶"""
        return self._group_api.pin_chat(app_id, top, chatroom_id)

    def set_msg_silence(self, app_id, silence, chatroom_id):
        """设置消息免打扰"""
        return self._group_api.set_msg_silence(app_id, silence, chatroom_id)

    def join_room_using_qr_code(self, app_id, qr_url):
        """扫码进群"""
        return self._group_api.join_room_using_qr_code(app_id, qr_url)

    def room_access_apply_check_approve(self, app_id, new_msg_id, chatroom_id, msg_content):
        """确认进群申请"""
        return self._group_api.room_access_apply_check_approve(app_id, new_msg_id, chatroom_id, msg_content)

    # Label API methods
    def add_label(self, app_id, label_name):
        """添加标签"""
        return self._label_api.add(app_id, label_name)

    def delete_label(self, app_id, label_ids):
        """删除标签"""
        return self._label_api.delete(app_id, label_ids)

    def list_labels(self, app_id):
        """获取标签列表"""
        return self._label_api.list(app_id)

    def modify_label_member_list(self, app_id, label_ids, wx_ids):
        """修改标签成员列表"""
        return self._label_api.modify_member_list(app_id, label_ids, wx_ids)

    # Personal API methods
    def get_profile(self, app_id):
        """获取个人资料"""
        return self._personal_api.get_profile(app_id)

    def get_qr_code(self, app_id):
        """获取自己的二维码"""
        return self._personal_api.get_qr_code(app_id)

    def get_safety_info(self, app_id):
        """获取设备记录"""
        return self._personal_api.get_safety_info(app_id)

    def privacy_settings(self, app_id, option, open):
        """隐私设置"""
        return self._personal_api.privacy_settings(app_id, option, open)

    def update_profile(self, app_id, city, country, nick_name, province, sex, signature):
        """修改个人信息"""
        return self._personal_api.update_profile(app_id, city, country, nick_name, province, sex, signature)

    def update_head_img(self, app_id, head_img_url):
        """修改头像"""
        return self._personal_api.update_head_img(app_id, head_img_url)

    # Login API methods
    def login(self, app_id):
        """登录"""
        return self._login_api.login(app_id)

    def get_token(self):
        """获取tokenId"""
        return self._login_api.get_token()

    def set_callback(self, token, callback_url):
        """设置微信消息的回调地址"""
        return self._login_api.set_callback(token, callback_url)

    def get_qr(self, app_id):
        """获取登录二维码"""
        return self._login_api.get_qr(app_id)

    def check_qr(self, app_id, uuid, captch_code):
        """确认登陆"""
        return self._login_api.check_qr(app_id, uuid, captch_code)

    def log_out(self, app_id):
        """退出微信"""
        return self._login_api.log_out(app_id)

    def dialog_login(self, app_id):
        """弹框登录"""
        return self._login_api.dialog_login(app_id)

    def check_online(self, app_id):
        """检查是否在线"""
        return self._login_api.check_online(app_id)

    def logout(self, app_id):
        """退出"""
        return self._login_api.logout(app_id)

    # Message API methods
    def post_text(self, app_id, to_wxid, content, ats: str = ""):
        """发送文字消息"""
        return self._message_api.post_text(app_id, to_wxid, content, ats)

    def post_file(self, app_id, to_wxid, file_url, file_name):
        """发送文件消息"""
        return self._message_api.post_file(app_id, to_wxid, file_url, file_name)

    def post_image(self, app_id, to_wxid, img_url):
        """发送图片消息"""
        return self._message_api.post_image(app_id, to_wxid, img_url)

    def post_voice(self, app_id, to_wxid, voice_url, voice_duration):
        """发送语音消息"""
        return self._message_api.post_voice(app_id, to_wxid, voice_url, voice_duration)

    def post_video(self, app_id, to_wxid, video_url, thumb_url, video_duration):
        """发送视频消息"""
        return self._message_api.post_video(app_id, to_wxid, video_url, thumb_url, video_duration)

    def post_link(self, app_id, to_wxid, title, desc, link_url, thumb_url):
        """发送链接消息"""
        return self._message_api.post_link(app_id, to_wxid, title, desc, link_url, thumb_url)

    def post_name_card(self, app_id, to_wxid, nick_name, name_card_wxid):
        """发送名片消息"""
        return self._message_api.post_name_card(app_id, to_wxid, nick_name, name_card_wxid)

    def post_emoji(self, app_id, to_wxid, emoji_md5, emoji_size):
        """发送emoji消息"""
        return self._message_api.post_emoji(app_id, to_wxid, emoji_md5, emoji_size)

    def post_app_msg(self, app_id, to_wxid, appmsg):
        """发送appmsg消息"""
        return self._message_api.post_app_msg(app_id, to_wxid, appmsg)

    def post_mini_app(self, app_id, to_wxid, mini_app_id, display_name, page_path, cover_img_url, title, user_name):
        """发送小程序消息"""
        return self._message_api.post_mini_app(app_id, to_wxid, mini_app_id, display_name, page_path, cover_img_url, title, user_name)

    def forward_file(self, app_id, to_wxid, xml):
        """转发文件"""
        return self._message_api.forward_file(app_id, to_wxid, xml)

    def forward_image(self, app_id, to_wxid, xml):
        """转发图片"""
        return self._message_api.forward_image(app_id, to_wxid, xml)

    def forward_video(self, app_id, to_wxid, xml):
        """转发视频"""
        return self._message_api.forward_video(app_id, to_wxid, xml)

    def forward_url(self, app_id, to_wxid, xml):
        """转发链接"""
        return self._message_api.forward_url(app_id, to_wxid, xml)

    def forward_mini_app(self, app_id, to_wxid, xml, cover_img_url):
        """转发小程序"""
        return self._message_api.forward_mini_app(app_id, to_wxid, xml, cover_img_url)

    def revoke_msg(self, app_id, to_wxid, msg_id, new_msg_id, create_time):
        """撤回消息"""
        return self._message_api.revoke_msg(app_id, to_wxid, msg_id, new_msg_id, create_time)
