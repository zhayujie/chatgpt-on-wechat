import requests

from . import storage

class Core(object):
    def __init__(self):
        ''' init is the only method defined in core.py
            alive is value showing whether core is running
                - you should call logout method to change it
                - after logout, a core object can login again
            storageClass only uses basic python types
                - so for advanced uses, inherit it yourself
            receivingRetryCount is for receiving loop retry
                - it's 5 now, but actually even 1 is enough
                - failing is failing
        '''
        self.alive, self.isLogging = False, False
        self.storageClass = storage.Storage(self)
        self.memberList = self.storageClass.memberList
        self.mpList = self.storageClass.mpList
        self.chatroomList = self.storageClass.chatroomList
        self.msgList = self.storageClass.msgList
        self.loginInfo = {}
        self.s = requests.Session()
        self.uuid = None
        self.functionDict = {'FriendChat': {}, 'GroupChat': {}, 'MpChat': {}}
        self.useHotReload, self.hotReloadDir = False, 'itchat.pkl'
        self.receivingRetryCount = 5
    def login(self, enableCmdQR=False, picDir=None, qrCallback=None,
            loginCallback=None, exitCallback=None):
        ''' log in like web wechat does
            for log in
                - a QR code will be downloaded and opened
                - then scanning status is logged, it paused for you confirm
                - finally it logged in and show your nickName
            for options
                - enableCmdQR: show qrcode in command line
                    - integers can be used to fit strange char length
                - picDir: place for storing qrcode
                - qrCallback: method that should accept uuid, status, qrcode
                - loginCallback: callback after successfully logged in
                    - if not set, screen is cleared and qrcode is deleted
                - exitCallback: callback after logged out
                    - it contains calling of logout
            for usage
                ..code::python

                    import itchat
                    itchat.login()

            it is defined in components/login.py
            and of course every single move in login can be called outside
                - you may scan source code to see how
                - and modified according to your own demand
        '''
        raise NotImplementedError()
    def get_QRuuid(self):
        ''' get uuid for qrcode
            uuid is the symbol of qrcode
                - for logging in, you need to get a uuid first
                - for downloading qrcode, you need to pass uuid to it
                - for checking login status, uuid is also required
            if uuid has timed out, just get another
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def get_QR(self, uuid=None, enableCmdQR=False, picDir=None, qrCallback=None):
        ''' download and show qrcode
            for options
                - uuid: if uuid is not set, latest uuid you fetched will be used
                - enableCmdQR: show qrcode in cmd
                - picDir: where to store qrcode
                - qrCallback: method that should accept uuid, status, qrcode
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def check_login(self, uuid=None):
        ''' check login status
            for options:
                - uuid: if uuid is not set, latest uuid you fetched will be used
            for return values:
                - a string will be returned
                - for meaning of return values
                    - 200: log in successfully
                    - 201: waiting for press confirm
                    - 408: uuid timed out
                    - 0  : unknown error
            for processing:
                - syncUrl and fileUrl is set
                - BaseRequest is set
            blocks until reaches any of above status
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def web_init(self):
        ''' get info necessary for initializing
            for processing:
                - own account info is set
                - inviteStartCount is set
                - syncKey is set
                - part of contact is fetched
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def show_mobile_login(self):
        ''' show web wechat login sign
            the sign is on the top of mobile phone wechat
            sign will be added after sometime even without calling this function
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def start_receiving(self, exitCallback=None, getReceivingFnOnly=False):
        ''' open a thread for heart loop and receiving messages
            for options:
                - exitCallback: callback after logged out
                    - it contains calling of logout
                - getReceivingFnOnly: if True thread will not be created and started. Instead, receive fn will be returned.
            for processing:
                - messages: msgs are formatted and passed on to registered fns
                - contact : chatrooms are updated when related info is received
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def get_msg(self):
        ''' fetch messages
            for fetching
                - method blocks for sometime until
                    - new messages are to be received
                    - or anytime they like
                - synckey is updated with returned synccheckkey
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def logout(self):
        ''' logout
            if core is now alive
                logout will tell wechat backstage to logout
            and core gets ready for another login
            it is defined in components/login.py
        '''
        raise NotImplementedError()
    def update_chatroom(self, userName, detailedMember=False):
        ''' update chatroom
            for chatroom contact
                - a chatroom contact need updating to be detailed
                - detailed means members, encryid, etc
                - auto updating of heart loop is a more detailed updating
                    - member uin will also be filled
                - once called, updated info will be stored
            for options
                - userName: 'UserName' key of chatroom or a list of it
                - detailedMember: whether to get members of contact
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def update_friend(self, userName):
        ''' update chatroom
            for friend contact
                - once called, updated info will be stored
            for options
                - userName: 'UserName' key of a friend or a list of it
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def get_contact(self, update=False):
        ''' fetch part of contact
            for part
                - all the massive platforms and friends are fetched
                - if update, only starred chatrooms are fetched
            for options
                - update: if not set, local value will be returned
            for results
                - chatroomList will be returned
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def get_friends(self, update=False):
        ''' fetch friends list
            for options
                - update: if not set, local value will be returned
            for results
                - a list of friends' info dicts will be returned
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def get_chatrooms(self, update=False, contactOnly=False):
        ''' fetch chatrooms list
            for options
                - update: if not set, local value will be returned
                - contactOnly: if set, only starred chatrooms will be returned
            for results
                - a list of chatrooms' info dicts will be returned
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def get_mps(self, update=False):
        ''' fetch massive platforms list
            for options
                - update: if not set, local value will be returned
            for results
                - a list of platforms' info dicts will be returned
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def set_alias(self, userName, alias):
        ''' set alias for a friend
            for options
                - userName: 'UserName' key of info dict
                - alias: new alias
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def set_pinned(self, userName, isPinned=True):
        ''' set pinned for a friend or a chatroom
            for options
                - userName: 'UserName' key of info dict
                - isPinned: whether to pin
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def accept_friend(self, userName, v4,autoUpdate=True):
        ''' accept a friend or accept a friend
            for options
                - userName: 'UserName' for friend's info dict
                - status:
                    - for adding status should be 2
                    - for accepting status should be 3
                - ticket: greeting message
                - userInfo: friend's other info for adding into local storage
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def get_head_img(self, userName=None, chatroomUserName=None, picDir=None):
        ''' place for docs
            for options
                - if you want to get chatroom header: only set chatroomUserName
                - if you want to get friend header: only set userName
                - if you want to get chatroom member header: set both
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def create_chatroom(self, memberList, topic=''):
        ''' create a chatroom
            for creating
                - its calling frequency is strictly limited
            for options
                - memberList: list of member info dict
                - topic: topic of new chatroom
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def set_chatroom_name(self, chatroomUserName, name):
        ''' set chatroom name
            for setting
                - it makes an updating of chatroom
                - which means detailed info will be returned in heart loop
            for options
                - chatroomUserName: 'UserName' key of chatroom info dict
                - name: new chatroom name
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def delete_member_from_chatroom(self, chatroomUserName, memberList):
        ''' deletes members from chatroom
            for deleting
                - you can't delete yourself
                - if so, no one will be deleted
                - strict-limited frequency
            for options
                - chatroomUserName: 'UserName' key of chatroom info dict
                - memberList: list of members' info dict
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def add_member_into_chatroom(self, chatroomUserName, memberList,
            useInvitation=False):
        ''' add members into chatroom
            for adding
                - you can't add yourself or member already in chatroom
                - if so, no one will be added
                - if member will over 40 after adding, invitation must be used
                - strict-limited frequency
            for options
                - chatroomUserName: 'UserName' key of chatroom info dict
                - memberList: list of members' info dict
                - useInvitation: if invitation is not required, set this to use
            it is defined in components/contact.py
        '''
        raise NotImplementedError()
    def send_raw_msg(self, msgType, content, toUserName):
        ''' many messages are sent in a common way
            for demo
                .. code:: python

                    @itchat.msg_register(itchat.content.CARD)
                    def reply(msg):
                        itchat.send_raw_msg(msg['MsgType'], msg['Content'], msg['FromUserName'])

            there are some little tricks here, you may discover them yourself
            but remember they are tricks
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def send_msg(self, msg='Test Message', toUserName=None):
        ''' send plain text message
            for options
                - msg: should be unicode if there's non-ascii words in msg
                - toUserName: 'UserName' key of friend dict
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def upload_file(self, fileDir, isPicture=False, isVideo=False,
            toUserName='filehelper', file_=None, preparedFile=None):
        ''' upload file to server and get mediaId
            for options
                - fileDir: dir for file ready for upload
                - isPicture: whether file is a picture
                - isVideo: whether file is a video
            for return values
                will return a ReturnValue
                if succeeded, mediaId is in r['MediaId']
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def send_file(self, fileDir, toUserName=None, mediaId=None, file_=None):
        ''' send attachment
            for options
                - fileDir: dir for file ready for upload
                - mediaId: mediaId for file. 
                    - if set, file will not be uploaded twice
                - toUserName: 'UserName' key of friend dict
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def send_image(self, fileDir=None, toUserName=None, mediaId=None, file_=None):
        ''' send image
            for options
                - fileDir: dir for file ready for upload
                    - if it's a gif, name it like 'xx.gif'
                - mediaId: mediaId for file. 
                    - if set, file will not be uploaded twice
                - toUserName: 'UserName' key of friend dict
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def send_video(self, fileDir=None, toUserName=None, mediaId=None, file_=None):
        ''' send video
            for options
                - fileDir: dir for file ready for upload
                    - if mediaId is set, it's unnecessary to set fileDir
                - mediaId: mediaId for file. 
                    - if set, file will not be uploaded twice
                - toUserName: 'UserName' key of friend dict
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def send(self, msg, toUserName=None, mediaId=None):
        ''' wrapped function for all the sending functions
            for options
                - msg: message starts with different string indicates different type
                    - list of type string: ['@fil@', '@img@', '@msg@', '@vid@']
                    - they are for file, image, plain text, video
                    - if none of them matches, it will be sent like plain text
                - toUserName: 'UserName' key of friend dict
                - mediaId: if set, uploading will not be repeated
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def revoke(self, msgId, toUserName, localId=None):
        ''' revoke message with its and msgId
            for options
                - msgId: message Id on server
                - toUserName: 'UserName' key of friend dict
                - localId: message Id at local (optional)
            it is defined in components/messages.py
        '''
        raise NotImplementedError()
    def dump_login_status(self, fileDir=None):
        ''' dump login status to a specific file
            for option
                - fileDir: dir for dumping login status
            it is defined in components/hotreload.py
        '''
        raise NotImplementedError()
    def load_login_status(self, fileDir,
            loginCallback=None, exitCallback=None):
        ''' load login status from a specific file
            for option
                - fileDir: file for loading login status
                - loginCallback: callback after successfully logged in
                    - if not set, screen is cleared and qrcode is deleted
                - exitCallback: callback after logged out
                    - it contains calling of logout
            it is defined in components/hotreload.py
        '''
        raise NotImplementedError()
    def auto_login(self, hotReload=False, statusStorageDir='itchat.pkl',
            enableCmdQR=False, picDir=None, qrCallback=None,
            loginCallback=None, exitCallback=None):
        ''' log in like web wechat does
            for log in
                - a QR code will be downloaded and opened
                - then scanning status is logged, it paused for you confirm
                - finally it logged in and show your nickName
            for options
                - hotReload: enable hot reload
                - statusStorageDir: dir for storing log in status
                - enableCmdQR: show qrcode in command line
                    - integers can be used to fit strange char length
                - picDir: place for storing qrcode
                - loginCallback: callback after successfully logged in
                    - if not set, screen is cleared and qrcode is deleted
                - exitCallback: callback after logged out
                    - it contains calling of logout
                - qrCallback: method that should accept uuid, status, qrcode
            for usage
                ..code::python

                    import itchat
                    itchat.auto_login()

            it is defined in components/register.py
            and of course every single move in login can be called outside
                - you may scan source code to see how
                - and modified according to your own demond
        '''
        raise NotImplementedError()
    def configured_reply(self):
        ''' determine the type of message and reply if its method is defined
            however, I use a strange way to determine whether a msg is from massive platform
            I haven't found a better solution here
            The main problem I'm worrying about is the mismatching of new friends added on phone
            If you have any good idea, pleeeease report an issue. I will be more than grateful.
        '''
        raise NotImplementedError()
    def msg_register(self, msgType,
            isFriendChat=False, isGroupChat=False, isMpChat=False):
        ''' a decorator constructor
            return a specific decorator based on information given
        '''
        raise NotImplementedError()
    def run(self, debug=True, blockThread=True):
        ''' start auto respond
            for option
                - debug: if set, debug info will be shown on screen
            it is defined in components/register.py
        '''
        raise NotImplementedError()
    def search_friends(self, name=None, userName=None, remarkName=None, nickName=None,
            wechatAccount=None):
        return self.storageClass.search_friends(name, userName, remarkName,
            nickName, wechatAccount)
    def search_chatrooms(self, name=None, userName=None):
        return self.storageClass.search_chatrooms(name, userName)
    def search_mps(self, name=None, userName=None):
        return self.storageClass.search_mps(name, userName)
