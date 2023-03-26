from .core import Core
from .config import VERSION, ASYNC_COMPONENTS
from .log import set_logging

if ASYNC_COMPONENTS:
    from .async_components import load_components
else:
    from .components import load_components


__version__ = VERSION


instanceList = []

def load_async_itchat() -> Core:
    """load async-based itchat instance

    Returns:
        Core: the abstract interface of itchat
    """
    from .async_components import load_components
    load_components(Core)
    return Core()


def load_sync_itchat() -> Core:
    """load sync-based itchat instance

    Returns:
        Core: the abstract interface of itchat
    """
    from .components import load_components
    load_components(Core)
    return Core()


if ASYNC_COMPONENTS:
    instance = load_async_itchat()
else:
    instance = load_sync_itchat()


instanceList = [instance]

# I really want to use sys.modules[__name__] = originInstance
# but it makes auto-fill a real mess, so forgive me for my following **
# actually it toke me less than 30 seconds, god bless Uganda

# components.login
login                       = instance.login
get_QRuuid                  = instance.get_QRuuid
get_QR                      = instance.get_QR
check_login                 = instance.check_login
web_init                    = instance.web_init
show_mobile_login           = instance.show_mobile_login
start_receiving             = instance.start_receiving
get_msg                     = instance.get_msg
logout                      = instance.logout
# components.contact
update_chatroom             = instance.update_chatroom
update_friend               = instance.update_friend
get_contact                 = instance.get_contact
get_friends                 = instance.get_friends
get_chatrooms               = instance.get_chatrooms
get_mps                     = instance.get_mps
set_alias                   = instance.set_alias
set_pinned                  = instance.set_pinned
accept_friend               = instance.accept_friend
get_head_img                = instance.get_head_img
create_chatroom             = instance.create_chatroom
set_chatroom_name           = instance.set_chatroom_name
delete_member_from_chatroom = instance.delete_member_from_chatroom
add_member_into_chatroom    = instance.add_member_into_chatroom
# components.messages
send_raw_msg                = instance.send_raw_msg
send_msg                    = instance.send_msg
upload_file                 = instance.upload_file
send_file                   = instance.send_file
send_image                  = instance.send_image
send_video                  = instance.send_video
send                        = instance.send
revoke                      = instance.revoke
# components.hotreload
dump_login_status           = instance.dump_login_status
load_login_status           = instance.load_login_status
# components.register
auto_login                  = instance.auto_login
configured_reply            = instance.configured_reply
msg_register                = instance.msg_register
run                         = instance.run
# other functions
search_friends              = instance.search_friends
search_chatrooms            = instance.search_chatrooms
search_mps                  = instance.search_mps
set_logging                 = set_logging
