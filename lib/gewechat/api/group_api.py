from ..util.http_util import post_json

class GroupApi:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def create_chatroom(self, app_id, wxids):
        """创建微信群"""
        param = {
            "appId": app_id,
            "wxids": wxids
        }
        return post_json(self.base_url, "/group/createChatroom", self.token, param)

    def modify_chatroom_name(self, app_id, chatroom_name, chatroom_id):
        """修改群名称"""
        param = {
            "appId": app_id,
            "chatroomName": chatroom_name,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/modifyChatroomName", self.token, param)

    def modify_chatroom_remark(self, app_id, chatroom_remark, chatroom_id):
        """修改群备注"""
        param = {
            "appId": app_id,
            "chatroomRemark": chatroom_remark,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/modifyChatroomRemark", self.token, param)

    def modify_chatroom_nickname_for_self(self, app_id, nick_name, chatroom_id):
        """修改我在群内的昵称"""
        param = {
            "appId": app_id,
            "nickName": nick_name,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/modifyChatroomNickNameForSelf", self.token, param)

    def invite_member(self, app_id, wxids, chatroom_id, reason):
        """邀请/添加 进群"""
        param = {
            "appId": app_id,
            "wxids": wxids,
            "reason": reason,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/inviteMember", self.token, param)

    def remove_member(self, app_id, wxids, chatroom_id):
        """删除群成员"""
        param = {
            "appId": app_id,
            "wxids": wxids,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/removeMember", self.token, param)

    def quit_chatroom(self, app_id, chatroom_id):
        """退出群聊"""
        param = {
            "appId": app_id,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/quitChatroom", self.token, param)

    def disband_chatroom(self, app_id, chatroom_id):
        """解散群聊"""
        param = {
            "appId": app_id,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/disbandChatroom", self.token, param)

    def get_chatroom_info(self, app_id, chatroom_id):
        """获取群信息"""
        param = {
            "appId": app_id,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/getChatroomInfo", self.token, param)

    def get_chatroom_member_list(self, app_id, chatroom_id):
        """获取群成员列表"""
        param = {
            "appId": app_id,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/getChatroomMemberList", self.token, param)

    def get_chatroom_member_detail(self, app_id, chatroom_id, member_wxids):
        """获取群成员详情"""
        param = {
            "appId": app_id,
            "memberWxids": member_wxids,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/getChatroomMemberDetail", self.token, param)

    def get_chatroom_announcement(self, app_id, chatroom_id):
        """获取群公告"""
        param = {
            "appId": app_id,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/getChatroomAnnouncement", self.token, param)

    def set_chatroom_announcement(self, app_id, chatroom_id, content):
        """设置群公告"""
        param = {
            "appId": app_id,
            "chatroomId": chatroom_id,
            "content": content
        }
        return post_json(self.base_url, "/group/setChatroomAnnouncement", self.token, param)

    def agree_join_room(self, app_id, url):
        """同意进群"""
        param = {
            "appId": app_id,
            "chatroomName": url
        }
        return post_json(self.base_url, "/group/agreeJoinRoom", self.token, param)

    def add_group_member_as_friend(self, app_id, member_wxid, chatroom_id, content):
        """添加群成员为好友"""
        param = {
            "appId": app_id,
            "memberWxid": member_wxid,
            "content": content,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/addGroupMemberAsFriend", self.token, param)

    def get_chatroom_qr_code(self, app_id, chatroom_id):
        """获取群二维码"""
        param = {
            "appId": app_id,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/getChatroomQrCode", self.token, param)

    def save_contract_list(self, app_id, oper_type, chatroom_id):
        """
        群保存到通讯录或从通讯录移除
        :param app_id: 设备id
        :param oper_type: 操作类型，3表示保存到通讯录，2表示从通讯录移除
        :param chatroom_id: 群id
        :return: API响应结果
        """
        param = {
            "appId": app_id,
            "operType": oper_type,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/saveContractList", self.token, param)

    def admin_operate(self, app_id, chatroom_id, wxids, oper_type):
        """管理员操作"""
        param = {
            "appId": app_id,
            "wxids": wxids,
            "operType": oper_type,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/adminOperate", self.token, param)

    def pin_chat(self, app_id, top, chatroom_id):
        """聊天置顶"""
        param = {
            "appId": app_id,
            "top": top,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/pinChat", self.token, param)

    def set_msg_silence(self, app_id, silence, chatroom_id):
        """设置消息免打扰"""
        param = {
            "appId": app_id,
            "silence": silence,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/setMsgSilence", self.token, param)

    def join_room_using_qr_code(self, app_id, qr_url):
        """扫码进群"""
        param = {
            "appId": app_id,
            "qrUrl": qr_url
        }
        return post_json(self.base_url, "/group/joinRoomUsingQRCode", self.token, param)

    def room_access_apply_check_approve(self, app_id, new_msg_id, chatroom_id, msg_content):
        """确认进群申请"""
        param = {
            "appId": app_id,
            "newMsgId": new_msg_id,
            "msgContent": msg_content,
            "chatroomId": chatroom_id
        }
        return post_json(self.base_url, "/group/roomAccessApplyCheckApprove", self.token, param)