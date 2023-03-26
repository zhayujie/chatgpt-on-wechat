import logging, copy, pickle
from weakref import ref

from ..returnvalues import ReturnValue
from ..utils import update_info_dict

logger = logging.getLogger('itchat')

class AttributeDict(dict):
    def __getattr__(self, value):
        keyName = value[0].upper() + value[1:]
        try:
            return self[keyName]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__.split('.')[-1], keyName))
    def get(self, v, d=None):
        try:
            return self[v]
        except KeyError:
            return d

class UnInitializedItchat(object):
    def _raise_error(self, *args, **kwargs):
        logger.warning('An itchat instance is called before initialized')
    def __getattr__(self, value):
        return self._raise_error

class ContactList(list):
    ''' when a dict is append, init function will be called to format that dict '''
    def __init__(self, *args, **kwargs):
        super(ContactList, self).__init__(*args, **kwargs)
        self.__setstate__(None)
    @property
    def core(self):
        return getattr(self, '_core', lambda: fakeItchat)() or fakeItchat
    @core.setter
    def core(self, value):
        self._core = ref(value)
    def set_default_value(self, initFunction=None, contactClass=None):
        if hasattr(initFunction, '__call__'):
            self.contactInitFn = initFunction
        if hasattr(contactClass, '__call__'):
            self.contactClass = contactClass
    def append(self, value):
        contact = self.contactClass(value)
        contact.core = self.core
        if self.contactInitFn is not None:
            contact = self.contactInitFn(self, contact) or contact
        super(ContactList, self).append(contact)
    def __deepcopy__(self, memo):
        r = self.__class__([copy.deepcopy(v) for v in self])
        r.contactInitFn = self.contactInitFn
        r.contactClass = self.contactClass
        r.core = self.core
        return r
    def __getstate__(self):
        return 1
    def __setstate__(self, state):
        self.contactInitFn = None
        self.contactClass = User
    def __str__(self):
        return '[%s]' % ', '.join([repr(v) for v in self])
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__.split('.')[-1],
            self.__str__())

class AbstractUserDict(AttributeDict):
    def __init__(self, *args, **kwargs):
        super(AbstractUserDict, self).__init__(*args, **kwargs)
    @property
    def core(self):
        return getattr(self, '_core', lambda: fakeItchat)() or fakeItchat
    @core.setter
    def core(self, value):
        self._core = ref(value)
    def update(self):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not be updated' % \
                self.__class__.__name__, }, })
    def set_alias(self, alias):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not set alias' % \
                self.__class__.__name__, }, })
    def set_pinned(self, isPinned=True):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not be pinned' % \
                self.__class__.__name__, }, })
    def verify(self):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s do not need verify' % \
                self.__class__.__name__, }, })
    def get_head_image(self, imageDir=None):
        return self.core.get_head_img(self.userName, picDir=imageDir)
    def delete_member(self, userName):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not delete member' % \
                self.__class__.__name__, }, })
    def add_member(self, userName):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not add member' % \
                self.__class__.__name__, }, })
    def send_raw_msg(self, msgType, content):
        return self.core.send_raw_msg(msgType, content, self.userName)
    def send_msg(self, msg='Test Message'):
        return self.core.send_msg(msg, self.userName)
    def send_file(self, fileDir, mediaId=None):
        return self.core.send_file(fileDir, self.userName, mediaId)
    def send_image(self, fileDir, mediaId=None):
        return self.core.send_image(fileDir, self.userName, mediaId)
    def send_video(self, fileDir=None, mediaId=None):
        return self.core.send_video(fileDir, self.userName, mediaId)
    def send(self, msg, mediaId=None):
        return self.core.send(msg, self.userName, mediaId)
    def search_member(self, name=None, userName=None, remarkName=None, nickName=None,
            wechatAccount=None):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s do not have members' % \
                self.__class__.__name__, }, })
    def __deepcopy__(self, memo):
        r = self.__class__()
        for k, v in self.items():
            r[copy.deepcopy(k)] = copy.deepcopy(v)
        r.core = self.core
        return r
    def __str__(self):
        return '{%s}' % ', '.join(
            ['%s: %s' % (repr(k),repr(v)) for k,v in self.items()])
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__.split('.')[-1],
            self.__str__())
    def __getstate__(self):
        return 1
    def __setstate__(self, state):
        pass
        
class User(AbstractUserDict):
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.__setstate__(None)
    def update(self):
        r = self.core.update_friend(self.userName)
        if r:
            update_info_dict(self, r)
        return r
    def set_alias(self, alias):
        return self.core.set_alias(self.userName, alias)
    def set_pinned(self, isPinned=True):
        return self.core.set_pinned(self.userName, isPinned)
    def verify(self):
        return self.core.add_friend(**self.verifyDict)
    def __deepcopy__(self, memo):
        r = super(User, self).__deepcopy__(memo)
        r.verifyDict = copy.deepcopy(self.verifyDict)
        return r
    def __setstate__(self, state):
        super(User, self).__setstate__(state)
        self.verifyDict = {}
        self['MemberList'] = fakeContactList

class MassivePlatform(AbstractUserDict):
    def __init__(self, *args, **kwargs):
        super(MassivePlatform, self).__init__(*args, **kwargs)
        self.__setstate__(None)
    def __setstate__(self, state):
        super(MassivePlatform, self).__setstate__(state)
        self['MemberList'] = fakeContactList

class Chatroom(AbstractUserDict):
    def __init__(self, *args, **kwargs):
        super(Chatroom, self).__init__(*args, **kwargs)
        memberList = ContactList()
        userName = self.get('UserName', '')
        refSelf = ref(self)
        def init_fn(parentList, d):
            d.chatroom = refSelf() or \
                parentList.core.search_chatrooms(userName=userName)
        memberList.set_default_value(init_fn, ChatroomMember)
        if 'MemberList' in self:
            for member in self.memberList:
                memberList.append(member)
        self['MemberList'] = memberList
    @property
    def core(self):
        return getattr(self, '_core', lambda: fakeItchat)() or fakeItchat
    @core.setter
    def core(self, value):
        self._core = ref(value)
        self.memberList.core = value
        for member in self.memberList:
            member.core = value
    def update(self, detailedMember=False):
        r = self.core.update_chatroom(self.userName, detailedMember)
        if r:
            update_info_dict(self, r)
            self['MemberList'] = r['MemberList']
        return r
    def set_alias(self, alias):
        return self.core.set_chatroom_name(self.userName, alias)
    def set_pinned(self, isPinned=True):
        return self.core.set_pinned(self.userName, isPinned)
    def delete_member(self, userName):
        return self.core.delete_member_from_chatroom(self.userName, userName)
    def add_member(self, userName):
        return self.core.add_member_into_chatroom(self.userName, userName)
    def search_member(self, name=None, userName=None, remarkName=None, nickName=None,
            wechatAccount=None):
        with self.core.storageClass.updateLock:
            if (name or userName or remarkName or nickName or wechatAccount) is None:
                return None
            elif userName: # return the only userName match
                for m in self.memberList:
                    if m.userName == userName:
                        return copy.deepcopy(m)
            else:
                matchDict = {
                    'RemarkName' : remarkName,
                    'NickName'   : nickName,
                    'Alias'      : wechatAccount, }
                for k in ('RemarkName', 'NickName', 'Alias'):
                    if matchDict[k] is None:
                        del matchDict[k]
                if name: # select based on name
                    contact = []
                    for m in self.memberList:
                        if any([m.get(k) == name for k in ('RemarkName', 'NickName', 'Alias')]):
                            contact.append(m)
                else:
                    contact = self.memberList[:]
                if matchDict: # select again based on matchDict
                    friendList = []
                    for m in contact:
                        if all([m.get(k) == v for k, v in matchDict.items()]):
                            friendList.append(m)
                    return copy.deepcopy(friendList)
                else:
                    return copy.deepcopy(contact)
    def __setstate__(self, state):
        super(Chatroom, self).__setstate__(state)
        if not 'MemberList' in self:
            self['MemberList'] = fakeContactList

class ChatroomMember(AbstractUserDict):
    def __init__(self, *args, **kwargs):
        super(AbstractUserDict, self).__init__(*args, **kwargs)
        self.__setstate__(None)
    @property
    def chatroom(self):
        r = getattr(self, '_chatroom', lambda: fakeChatroom)()
        if r is None:
            userName = getattr(self, '_chatroomUserName', '')
            r = self.core.search_chatrooms(userName=userName)
            if isinstance(r, dict):
                self.chatroom = r
        return r or fakeChatroom
    @chatroom.setter
    def chatroom(self, value):
        if isinstance(value, dict) and 'UserName' in value:
            self._chatroom = ref(value)
            self._chatroomUserName = value['UserName']
    def get_head_image(self, imageDir=None):
        return self.core.get_head_img(self.userName, self.chatroom.userName, picDir=imageDir)
    def delete_member(self, userName):
        return self.core.delete_member_from_chatroom(self.chatroom.userName, self.userName)
    def send_raw_msg(self, msgType, content):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not send message directly' % \
                self.__class__.__name__, }, })
    def send_msg(self, msg='Test Message'):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not send message directly' % \
                self.__class__.__name__, }, })
    def send_file(self, fileDir, mediaId=None):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not send message directly' % \
                self.__class__.__name__, }, })
    def send_image(self, fileDir, mediaId=None):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not send message directly' % \
                self.__class__.__name__, }, })
    def send_video(self, fileDir=None, mediaId=None):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not send message directly' % \
                self.__class__.__name__, }, })
    def send(self, msg, mediaId=None):
        return ReturnValue({'BaseResponse': {
            'Ret': -1006,
            'ErrMsg': '%s can not send message directly' % \
                self.__class__.__name__, }, })
    def __setstate__(self, state):
        super(ChatroomMember, self).__setstate__(state)
        self['MemberList'] = fakeContactList

def wrap_user_dict(d):
    userName = d.get('UserName')
    if '@@' in userName:
        r = Chatroom(d)
    elif d.get('VerifyFlag', 8) & 8 == 0:
        r = User(d)
    else:
        r = MassivePlatform(d)
    return r

fakeItchat = UnInitializedItchat()
fakeContactList = ContactList()
fakeChatroom = Chatroom()
