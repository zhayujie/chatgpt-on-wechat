class NoneBotRawMessage:
    """
    与 chat_message 类属性基本一致
    """
    msg_id = None,
    create_time = None,
    ctype = None,
    content = None,
    from_user_id = None,
    from_user_nickname = None,
    to_user_id = None,
    to_user_nickname = None,
    group_id = None,
    group_nickname = None,
    is_group = False,
    is_at = False

    def __init__(
            self,
            msg_id=None,
            create_time=None,
            ctype=None,
            content=None,
            from_user_id=None,
            from_user_nickname=None,
            to_user_id=None,
            to_user_nickname=None,
            group_id=None,
            group_nickname=None,
            is_group=False,
            is_at=False
    ):
        self.msg_id = msg_id
        self.create_time = create_time
        self.ctype = ctype
        self.content = content
        self.from_user_id = from_user_id
        self.from_user_nickname = from_user_nickname
        self.to_user_id = to_user_id
        self.to_user_nickname = to_user_nickname
        self.group_id = group_id
        self.group_nickname = group_nickname
        self.is_group = is_group
        self.is_at = is_at

    # get方法
    def get(self, key):
        return self.__dict__.get(key)
