import os.path

from common.log import logger
from tools.tool import tool


@tool("Send message to user", return_direct=False, version=0.1, author="goldfish")
def send_message(query: str):
    """
        useful when you know the user ID to whom you want to send a message.
        if you don't know user ID, do not use this tool.
        The input to this tool should be a comma separated string of two,
        representing the message you want to send, the user ID.
    """
    msg, user_id = query.split(",")
    if not msg or not user_id:
        return "you should use a comma to separate message and user ID"

    logger.info('[WX] sendMsg={}, user ID={}'.format(msg, user_id))
    try:
        import itchat

        itchat.send(msg, toUserName=user_id)
    except:
        return "send message failed."


@tool("Send picture to user", return_direct=False, version=0.1, author="goldfish")
def send_picture(query: str):
    """
        useful when you know the user ID to whom you want to send a picture.
        if you don't know user ID, do not use this tool.
        The input to this tool should be a comma separated string of two,
        representing the image_path and the user ID.
    """
    image_path, user_id = query.split(",")
    if not image_path or not user_id:
        return "you should use a comma to separate image_path and user ID."

    if not os.path.exists(image_path):
        return "the image_path is illegal."

    logger.info('[WX] image_path={}, user ID={}'.format(image_path, user_id))
    try:
        import itchat

        itchat.send_image(image_path, toUserName=user_id)
    except:
        return "send picture failed."
